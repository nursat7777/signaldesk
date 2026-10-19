import {beforeEach,describe,it,expect,vi} from 'vitest';
import {render,screen} from '@testing-library/react';
import {createApiService,type AuthService} from './api-service';
import {AuthGate} from './AuthGate';
import {createMockService,daysAgo,ServiceError} from './service';
beforeEach(()=>localStorage.clear());
describe('Independent QA REST boundary',()=>{
 it('maps all13 service operations, cookies, CSRF and exact wire amounts',async()=>{
 const calls:{url:string;init:RequestInit}[]=[];const date=daysAgo(0);const metric={id:'m1',campaignId:'p/a',date,spend:'10.25',revenue:'30.75',impressions:100,clicks:5,leads:2,sales:1,version:1};
 const fetcher=vi.fn(async(url:RequestInfo|URL,init?:RequestInit)=>{calls.push({url:String(url),init:init!});const path=String(url);if(path.endsWith('/assignments'))return new Response(null,{status:204});const body=path.includes('/metrics?')?[metric]:path.includes('/metrics/')?metric:path.endsWith('/me')?{id:'u1'}:[];return new Response(JSON.stringify(body),{status:200,headers:{'Content-Type':'application/json',...(path.endsWith('/me')?{'X-CSRF-Token':'qa-csrf'}:{})}});}) as typeof fetch;
 const api=createApiService('/api',fetcher);await api.getMe();await api.listClients();await api.createClient({name:'QA',currency:'USD'});await api.updateClient('c/a',{archived:true});await api.listCampaigns('c/a');await api.createCampaign({clientId:'c/a',name:'QA',channel:'Other'});await api.updateCampaign('p/a',{name:'Renamed'});const listed=await api.listMetrics('c/a',date,date);expect(listed[0].spend).toBe(10.25);const saved=await api.saveMetric({campaignId:'p/a',date,spend:10.25,revenue:30.75,impressions:100,clicks:5,leads:2,sales:1});expect(saved.revenue).toBe(30.75);await api.listUsers();await api.createUser({name:'QA',email:'qa@example.com',role:'client',clientId:'c/a'});await api.updateUser('u/a',{enabled:false});await api.setAssignments('u/a',['c/a']);expect(calls).toHaveLength(13);
 for(const call of calls){expect(call.init.credentials).toBe('include');if(call.init.method!=='GET')expect(call.init.headers).toMatchObject({'X-CSRF-Token':'qa-csrf'});}
 expect(calls[3].url).toBe('/api/clients/c%2Fa');expect(calls[8].url).toBe(`/api/campaigns/p%2Fa/metrics/${date}`);expect(JSON.parse(String(calls[8].init.body))).toMatchObject({spend:'10.25',revenue:'30.75'});expect(JSON.parse(String(calls[5].init.body))).not.toHaveProperty('clientId');
 });
 it('propagates stable HTTP failures and network errors without mock fallback',async()=>{const denied=createApiService('/api',vi.fn(async()=>new Response(JSON.stringify({code:'conflict',message:'stale'}),{status:409})) as typeof fetch);await expect(denied.listClients()).rejects.toMatchObject({code:'conflict'});const offline=createApiService('/api',vi.fn(async()=>{throw new Error('offline')}) as typeof fetch);await expect(offline.listClients()).rejects.toMatchObject({code:'network'});});
});
function auth(configured:boolean):AuthService{const m=createMockService();return {...m.service,getMe:vi.fn(async()=>{throw new ServiceError('unauthorized')}),authStatus:async()=>({configured}),logout:async()=>{},loginUrl:'/api/auth/google'}}
describe('Independent QA production auth shell',()=>{
 it('shows setup required with no mock accounts when OAuth is missing',async()=>{render(<AuthGate api={auth(false)}/>);await screen.findByText('Google sign-in needs configuration');expect(screen.queryByText(/MOCK DATA/)).not.toBeInTheDocument();expect(screen.queryByRole('combobox')).not.toBeInTheDocument();expect(screen.queryByRole('link',{name:/Continue with Google/})).not.toBeInTheDocument();});
 it('401 exposes Google route only when configuration exists',async()=>{render(<AuthGate api={auth(true)}/>);expect(await screen.findByRole('link',{name:/Continue with Google/})).toHaveAttribute('href','/api/auth/google');expect(screen.queryByText('Performance intelligence')).not.toBeInTheDocument();});
});
