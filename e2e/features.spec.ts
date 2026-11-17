import { test, expect, entry, save, api } from './fixtures';

test('E01 #29 authentication state and real session logout',async({page,login})=>{
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Sign in to your workspace'})).toBeVisible();
  expect((await page.request.get('/api/me')).status()).toBe(401);
  await login(); await page.getByRole('button',{name:'Sign out',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Sign in to your workspace'})).toBeVisible();
  expect((await page.request.get('/api/me')).status()).toBe(401);
});
test('E02 #30 role navigation and cross-client denial',async({page,login,data})=>{
  await login('client');
  await expect(page.getByRole('button',{name:'Agency settings',exact:true})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Add daily results',exact:true})).toHaveCount(0);
  expect((await page.request.get(`/api/clients/${data.otherId}/campaigns`)).status()).toBe(403);
});
test('E03 #31 create client and require name',async({page,login,data})=>{
  await login();await page.getByRole('button',{name:'Agency settings',exact:true}).click();
  await page.getByRole('button',{name:'Add client',exact:true}).click();
  await page.getByRole('button',{name:'Save changes',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByLabel('Name',{exact:true}).fill(data.key+' Created');
  await page.getByLabel('Currency',{exact:true}).selectOption('EUR');await save(page);
  const rows=await (await page.request.get('/api/clients')).json();
  expect(rows.find((c:any)=>c.name===data.key+' Created').currency).toBe('EUR');
});
test('E04 #32 archive and restore client',async({page,login,data})=>{
  await login();await page.getByRole('button',{name:'Agency settings',exact:true}).click();
  const row=page.locator('.client-row').filter({hasText:data.key+' client'});
  await row.getByRole('button',{name:'Archive',exact:true}).click();
  await expect(row.getByRole('button',{name:'Restore',exact:true})).toBeVisible();
  await row.getByRole('button',{name:'Restore',exact:true}).click();
  await expect(row.getByRole('button',{name:'Archive',exact:true})).toBeVisible();
});
test('E05 #33 approve user and revoke access',async({page,login,data})=>{
  await login();await page.getByRole('button',{name:'Agency settings',exact:true}).click();
  await page.getByRole('button',{name:'Approve account',exact:true}).click();
  await page.getByLabel('Name',{exact:true}).fill(data.key+' New');
  await page.getByLabel('Email',{exact:true}).fill(data.key+'new@fixture.test');await save(page);
  const row=page.locator('.user-row').filter({hasText:data.key+'new@fixture.test'});
  await row.getByRole('button',{name:'Revoke access',exact:true}).click();
  await expect(row.getByRole('button',{name:'Enable access',exact:true})).toBeVisible();
});
test('E06 #34 revoke and restore marketer assignment',async({page,login,data})=>{
  await login();await page.getByRole('button',{name:'Agency settings',exact:true}).click();
  const row=page.locator('.user-row').filter({hasText:data.key+'-marketer@fixture.test'});
  await row.getByLabel(data.key+' client',{exact:true}).uncheck();
  await row.getByRole('button',{name:'Save assignments',exact:true}).click();
  const users=await (await page.request.get('/api/users')).json();
  expect(users.find((u:any)=>u.id===data.key+'-marketer').clientIds).toEqual([]);
  await row.getByLabel(data.key+' client',{exact:true}).check();
  await row.getByRole('button',{name:'Save assignments',exact:true}).click();
  await expect(page.getByRole('status')).toContainText('Changes saved');
});
test('E07 #35 create campaign and validate required name',async({page,login,data})=>{
  await login('marketer');await page.getByRole('button',{name:'New campaign',exact:true}).click();
  await page.getByRole('button',{name:'Save changes',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByLabel('Name',{exact:true}).fill(data.key+' Meta');
  await page.getByLabel('Channel',{exact:true}).selectOption('Meta Ads');await save(page);
  await expect(page.getByText(data.key+' Meta',{exact:true})).toBeVisible();
});
test('E08 #36 archive and restore campaign',async({page,login,data})=>{
  await login();const row=page.getByRole('row').filter({hasText:data.key+' Search'});
  await row.getByRole('button',{name:'Archive',exact:true}).click();
  await expect(row.getByRole('button',{name:'Edit',exact:true})).toBeDisabled();
  await row.getByRole('button',{name:'Restore',exact:true}).click();
  await expect(row.getByRole('button',{name:'Edit',exact:true})).toBeEnabled();
});
test('E09 #37 campaign search and no-match state',async({page,login,data})=>{
  await login();await page.getByRole('button',{name:'Campaigns',exact:true}).click();
  await page.getByLabel('Search campaigns',{exact:true}).fill('SEARCH');
  await expect(page.getByText(data.key+' Search',{exact:true})).toBeVisible();
  await page.getByLabel('Search campaigns',{exact:true}).fill('absent-name');
  await expect(page.getByText('No campaigns yet',{exact:true})).toBeVisible();
  await page.getByLabel('Search campaigns',{exact:true}).fill('');
  await expect(page.getByText(data.key+' Search',{exact:true})).toBeVisible();
});
test('E10 #38 daily values, validation and exact persisted money',async({page,login,data})=>{
  await login();await entry(page,'-1');
  await page.getByRole('button',{name:'Save changes',exact:true}).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByLabel('Ad spend',{exact:true}).fill('12.34');await save(page);
  const rows=await (await page.request.get(`/api/clients/${data.clientId}/metrics?from=2000-01-01&to=2099-12-31`)).json();
  expect(rows[0].spend).toBe('12.34');expect(rows[0].revenue).toBe('37.02');
});
test('E11 #39 duplicate date loads row and increments version',async({page,login,data})=>{
  await login();await entry(page);await save(page);await entry(page,'20');
  await expect(page.getByText('Existing record loaded. Saving updates this date.')).toBeVisible();await save(page);
  const rows=await (await page.request.get(`/api/clients/${data.clientId}/metrics?from=2000-01-01&to=2099-12-31`)).json();
  expect(rows).toHaveLength(1);expect(rows[0].version).toBe(2);expect(rows[0].spend).toBe('20.00');
});
test('E12 #40 concurrent edits reject stale browser',async({page,browser,login,data})=>{
  await login();await entry(page);await save(page);
  const context=await browser.newContext();const other=await context.newPage();
  await login('admin',other);await entry(page,'40');await entry(other,'50');await save(page);
  await other.getByRole('button',{name:'Save changes',exact:true}).click();
  await expect(other.getByRole('dialog').getByRole('alert')).toContainText('This record changed');
  await expect(other.getByLabel('Ad spend',{exact:true})).toHaveValue('50');await context.close();
});
test('E13 #41 inclusive date filter, invalid range and reset',async({page,login})=>{
  await login();await entry(page);await save(page);
  await page.getByLabel('From',{exact:true}).fill('2000-01-01');await page.getByLabel('To',{exact:true}).fill('2000-01-02');
  await expect(page.getByText('No results in this period',{exact:true})).toBeVisible();
  await page.getByLabel('From',{exact:true}).fill('2001-01-01');
  await expect(page.getByRole('alert')).toContainText('Start date must not follow');
  await page.getByRole('button',{name:'Last 30 days',exact:true}).click();
  await expect(page.getByRole('alert')).toHaveCount(0);
});
test('E14 #42 totals and zero-denominator rendering',async({page,login,data})=>{
  await login();await expect(page.locator('.kpi-value').last()).toHaveText('—');
  await entry(page);await save(page);
  await expect(page.locator('.kpi-value').first()).toContainText('12.34');
  await expect(page.locator('.kpi-value').last()).toContainText('3');
  // Verify the real report API against the same persisted values shown in the UI.
  const reportPath=`/api/clients/${data.clientId}/report?from=2000-01-01&to=2099-12-31`;
  const response=await page.request.get(reportPath);
  expect(response.status()).toBe(200);
  const report=await response.json();
  expect(report.totals.spend).toBe('12.34');
  expect(report.totals.revenue).toBe('37.02');
  expect(report.totals.roas).toBe(3);
  expect(report.daily).toHaveLength(1);
  expect((await page.request.get(`/api/clients/${data.clientId}/report?from=2001-01-01&to=2000-01-01`)).status()).toBe(422);
  await login('client');
  expect((await page.request.get(reportPath)).status()).toBe(200);
  expect((await page.request.get(`/api/clients/${data.otherId}/report?from=2000-01-01&to=2099-12-31`)).status()).toBe(403);
});
test('E15 #43 channel comparison uses persisted totals',async({page,login})=>{
  await login();await entry(page);await save(page);await page.getByRole('button',{name:'Channels',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Channel comparison',exact:true})).toBeVisible();
  await expect(page.getByRole('row').filter({hasText:'Google Ads'})).toContainText('12.34');
  await expect(page.getByRole('row').filter({hasText:'Meta Ads'})).toContainText('0.00');
});
test('E16 #44 language persistence and mobile navigation',async({page,login})=>{
  await login();await page.getByRole('button',{name:'English RU',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Аналитика эффективности',exact:true})).toBeVisible();
  await page.reload();await expect(page.getByRole('heading',{name:'Аналитика эффективности',exact:true})).toBeVisible();
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('button',{name:'Каналы',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Сравнение каналов',exact:true})).toBeVisible();
});
test('E17 #45 reload preserves database metric and session',async({page,login,data})=>{
  await login('marketer');await entry(page,'25.67');await save(page);await page.reload();
  await expect(page.locator('.kpi-value').first()).toContainText('25.67');
  expect((await page.request.get('/api/me')).status()).toBe(200);
  const rows=await (await page.request.get(`/api/clients/${data.clientId}/metrics?from=2000-01-01&to=2099-12-31`)).json();expect(rows).toHaveLength(1);
});
