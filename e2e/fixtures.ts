import { test as base, expect, Page } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
type Role = 'admin' | 'marketer' | 'client';
export type Fixture = { key: string; clientId: string; otherId: string; campaignId: string; sessions: Record<Role,{token:string;csrf:string}> };
export const test = base.extend<{ data: Fixture; login: (role?: Role, page?: Page)=>Promise<void> }>({
  data: async ({}, use) => {
    const url = process.env.E2E_TEST_DATABASE_URL || `sqlite:///${resolve('.e2e-test.sqlite3')}`;
    const data = JSON.parse(execFileSync(process.env.TEST_PYTHON || '.venv/bin/python', ['-m','scripts.e2e_seed'], {env:{...process.env,E2E_TEST_DATABASE_URL:url},encoding:'utf8'}));
    await use(data);
  },
  login: async ({page, data, baseURL}, use) => {
    await use(async (role='admin', target=page) => {
      await target.context().addCookies([{name:'signaldesk_session',value:data.sessions[role].token,url:baseURL!,httpOnly:true,sameSite:'Lax'}]);
      await target.goto('/');
      await expect(target.getByRole('heading',{name:'Performance intelligence',exact:true})).toBeVisible();
      await target.getByLabel('Clients',{exact:true}).selectOption(data.clientId);
      await expect(target.getByText(`${data.key} Search`,{exact:true})).toBeVisible();
    });
  },
});
export { expect };
export async function entry(page:Page, spend='12.34') {
  await page.getByRole('button',{name:'Add daily results',exact:true}).click();
  for(const [label,value] of Object.entries({'Ad spend':spend,'Impressions':'100','Clicks':'10','Leads':'2','Sales':'1','Revenue':'37.02'})) await page.getByLabel(label,{exact:true}).fill(value);
}
export async function save(page:Page) {
  await page.getByRole('button',{name:'Save changes',exact:true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('status')).toContainText('Changes saved');
}
export async function api(page:Page,data:Fixture,path:string,method='GET',body?:unknown,role:Role='admin') {
  return page.request.fetch(path,{method,data:body,headers:{Origin:new URL(page.url()).origin,'X-CSRF-Token':data.sessions[role].csrf}});
}
