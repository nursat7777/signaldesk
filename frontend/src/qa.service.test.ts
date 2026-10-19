import { describe, it, expect } from 'vitest';
import {createMockService,aggregate,daysAgo,validateMetric,type MetricInput} from './service';
const input=():MetricInput=>({campaignId:'p1',date:daysAgo(40),spend:10.25,impressions:100,clicks:20,leads:4,sales:2,revenue:30});
describe('Independent QA service acceptance',()=>{
 it('isolates each role and disallows client mutation',async()=>{const m=createMockService();m.setIdentity('u2');expect((await m.service.listClients()).map(c=>c.id)).toEqual(['c1','c2']);await expect(m.service.listCampaigns('c3')).rejects.toMatchObject({code:'forbidden'});await expect(m.service.listUsers()).rejects.toMatchObject({code:'forbidden'});m.setIdentity('u3');expect((await m.service.listClients()).map(c=>c.id)).toEqual(['c1']);await expect(m.service.saveMetric(input())).rejects.toMatchObject({code:'forbidden'});await expect(m.service.listMetrics('c2',daysAgo(30),daysAgo(0))).rejects.toMatchObject({code:'forbidden'});});
 it('enforces unique day and optimistic version; inclusive filters',async()=>{const {service:s}=createMockService();const row=await s.saveMetric(input());await expect(s.saveMetric(input())).rejects.toMatchObject({code:'conflict'});const updated=await s.saveMetric({...input(),version:row.version,spend:20});expect(updated.version).toBe(2);await expect(s.saveMetric({...input(),version:1})).rejects.toMatchObject({code:'conflict'});expect(await s.listMetrics('c1',row.date,row.date)).toEqual([updated]);});
 it('preserves archived history, disallows metric writes and currency changes',async()=>{const {service:s}=createMockService();await s.updateCampaign('p1',{archived:true});await expect(s.saveMetric(input())).rejects.toMatchObject({code:'archived'});expect((await s.listMetrics('c1',daysAgo(30),daysAgo(0))).length).toBe(90);await expect(s.updateClient('c1',{currency:'USD'})).rejects.toMatchObject({code:'currencyLocked'});});
 it('rechecks revocation and assignment immediately',async()=>{const m=createMockService();await m.service.setAssignments('u2',['c1']);m.setIdentity('u2');await expect(m.service.listCampaigns('c2')).rejects.toMatchObject({code:'forbidden'});m.setIdentity('u1');await m.service.updateUser('u2',{enabled:false});m.setIdentity('u2');await expect(m.service.getMe()).rejects.toMatchObject({code:'forbidden'});});
 it('calculates weighted ratios, unavailable zeros and strict metrics',()=>{const a={...input(),id:'1',version:1};const b={...a,spend:90,clicks:10,impressions:900,leads:6,revenue:70};const sum=aggregate([a,b]);expect(sum.ctr).toBe(3);expect(sum.cpc).toBeCloseTo(100.25/30);expect(aggregate([]).roas).toBeNull();for(const change of [{date:'2026-02-30'},{spend:-1},{clicks:1.1},{revenue:1.001},{leads:NaN},{date:'2999-01-01'}])expect(()=>validateMetric({...input(),...change})).toThrow();expect(()=>validateMetric({...input(),clicks:200,sales:30})).not.toThrow();});
});

describe('Independent QA account relationship invariants',()=>{
 it('rejects changing marketer to client viewer without valid client association',async()=>{const {service:s}=createMockService();await expect(s.updateUser('u2',{role:'client',clientId:null})).rejects.toMatchObject({code:'required'});});
 it('rejects replacing viewer association with nonexistent client',async()=>{const {service:s}=createMockService();await expect(s.updateUser('u3',{clientId:'missing'})).rejects.toMatchObject({code:'required'});});
});

describe('B01 independent role-transition regression',()=>{
 it('rejected patch preserves state',async()=>{const {service:s}=createMockService();const before=await s.listUsers();await expect(s.updateUser('u2',{role:'client',clientId:null})).rejects.toThrow();expect(await s.listUsers()).toEqual(before);});
 it('clears previous assignments and irrelevant association on role changes',async()=>{const {service:s}=createMockService();const viewer=await s.updateUser('u2',{role:'client',clientId:'c1'});expect(viewer.clientIds).toEqual([]);const marketer=await s.updateUser('u2',{role:'marketer'});expect(marketer.clientId).toBeNull();expect(marketer.clientIds).toEqual([]);const admin=await s.updateUser('u3',{role:'admin'});expect(admin.clientId).toBeNull();});
});

describe('Independent QA monetary range parity',()=>{
 it('accepts valid large two-decimal amounts within contract limit',()=>{for(const spend of [123456789012.35,999999999999.99])expect(()=>validateMetric({...input(),spend})).not.toThrow();});
});
