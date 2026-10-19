import {afterAll,beforeAll,beforeEach,describe,it,expect} from 'vitest';
import {render,screen,within,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {AuthGate} from './AuthGate';
import {today} from './service';
import {startHttpFixture} from '../test-support/server';
let fixture:Awaited<ReturnType<typeof startHttpFixture>>;
beforeAll(async()=>{fixture=await startHttpFixture()},30000);
afterAll(async()=>{await fixture?.stop()},15000);
beforeEach(()=>localStorage.clear());
describe('Independent QA actualHTTP SQLite workflow',()=>{
 it('admin creates campaign; marketer enters results; viewer reads own report only',async()=>{
 const user=userEvent.setup();const admin=fixture.api('admin');let view=render(<AuthGate api={admin}/>);
 await screen.findByText('Performance intelligence');await user.click(await screen.findByRole('button',{name:'New campaign'}));let dialog=screen.getByRole('dialog');await user.type(within(dialog).getByLabelText('Name'),'QA Real HTTP Campaign');await user.selectOptions(within(dialog).getByLabelText('Channel'),'Other');await user.click(within(dialog).getByRole('button',{name:'Save changes'}));await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());await screen.findByText('QA Real HTTP Campaign');view.unmount();
 const marketer=fixture.api('marketer');view=render(<AuthGate api={marketer}/>);await screen.findByText('QA Real HTTP Campaign');await user.click(screen.getByRole('button',{name:'Add daily results'}));dialog=screen.getByRole('dialog');await waitFor(()=>expect(within(dialog).getByLabelText('Ad spend')).toHaveValue(null));for(const [label,value] of [['Ad spend','10.25'],['Impressions','100'],['Clicks','20'],['Leads','4'],['Sales','2'],['Revenue','35.75']])await user.type(within(dialog).getByLabelText(label),value);await user.click(within(dialog).getByRole('button',{name:'Save changes'}));await waitFor(()=>expect(screen.queryByRole('dialog')).not.toBeInTheDocument());await screen.findAllByText(/KZT\s10\.25/);view.unmount();
 const viewer=fixture.api('client');view=render(<AuthGate api={viewer}/>);await screen.findByText('QA Real HTTP Campaign');expect(screen.queryByRole('button',{name:'Add daily results'})).not.toBeInTheDocument();expect(screen.queryByRole('button',{name:'Agency settings'})).not.toBeInTheDocument();const select=screen.getByRole('combobox',{name:'Clients'});expect(within(select).getAllByRole('option')).toHaveLength(1);expect(select).toHaveValue(fixture.metadata.clientId);await screen.findAllByText(/KZT\s10\.25/);await expect(viewer.listMetrics(fixture.metadata.otherClientId,today(),today())).rejects.toMatchObject({code:'forbidden'});await user.click(screen.getByRole('button',{name:/English/}));await screen.findByText('Аналитика эффективности');view.unmount();
 const rows=await marketer.listMetrics(fixture.metadata.clientId,today(),today());expect(rows).toHaveLength(1);expect(rows[0].spend).toBe(10.25);expect(rows[0].revenue).toBe(35.75);expect(fixture.requests.some(r=>r.method==='PUT'&&r.path.includes('/metrics/'))).toBe(true);
 },20000);
 it('real API rejects revoked assignments, unconfigured unauthenticated entry and stale writes',async()=>{const admin=fixture.api('admin');await admin.getMe();const marketer=fixture.api('marketer');await marketer.getMe();const rows=await marketer.listMetrics(fixture.metadata.clientId,today(),today());expect(rows).toHaveLength(1);const row=rows[0];await expect(marketer.saveMetric({...row,version:undefined})).rejects.toMatchObject({code:'conflict'});await admin.setAssignments(fixture.metadata.sessions.marketer.userId,[]);expect(await marketer.listClients()).toEqual([]);await expect(marketer.listCampaigns(fixture.metadata.clientId)).rejects.toMatchObject({code:'forbidden'});render(<AuthGate api={fixture.unauthApi()}/>);await screen.findByText('Google sign-in needs configuration');expect(screen.queryByRole('combobox')).not.toBeInTheDocument();},15000);
});
