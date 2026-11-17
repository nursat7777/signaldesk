import { describe, it, expect } from 'vitest';
import { render, screen, within, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from './App';
import { createMockService } from './service';

async function open(api: ReturnType<typeof createMockService>['service']) {
  const user = userEvent.setup();
  render(<App api={api} demo={false} />);
  const button = await screen.findByRole('button', { name: 'Add daily results' });
  await waitFor(() => expect(button).toBeEnabled());
  await user.click(button);
  return { user, dialog: within(screen.getByRole('dialog')) };
}

describe('Metric lookup safety regression #68', () => {
  it('prevents editing and saving until the selected day lookup finishes', async () => {
    const m = createMockService();
    const original = m.service.listMetrics.bind(m.service);
    let release!: () => void;
    m.service.listMetrics = async (client, from, to) => {
      if (from === to) await new Promise<void>(resolve => { release = resolve; });
      return original(client, from, to);
    };
    const { user, dialog } = await open(m.service);
    const spend = dialog.getByLabelText('Ad spend');
    expect(spend).toBeDisabled();
    expect(dialog.getByRole('button', { name: 'Save changes' })).toBeDisabled();
    await act(async () => release());
    await waitFor(() => expect(spend).toBeEnabled());
    await user.clear(spend);
    await user.type(spend, '123.45');
    expect(spend).toHaveValue(123.45);
  });

  it('does not allow saving stale values after a lookup failure', async () => {
    const m = createMockService();
    const original = m.service.listMetrics.bind(m.service);
    m.service.listMetrics = async (client, from, to) => {
      if (from === to) throw new Error('disposable simulated transport failure');
      return original(client, from, to);
    };
    const { dialog } = await open(m.service);
    await waitFor(() => expect(dialog.getByRole('alert')).toBeVisible());
    expect(dialog.getByLabelText('Ad spend')).toBeDisabled();
    expect(dialog.getByRole('button', { name: 'Save changes' })).toBeDisabled();
  });
});
