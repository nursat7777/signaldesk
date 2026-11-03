import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1,
  forbidOnly: !!process.env.CI, retries: 0, timeout: 30000,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:8000', trace: 'retain-on-failure', screenshot: 'only-on-failure', video: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: process.env.E2E_BASE_URL ? undefined : {
    command: '.venv/bin/python -m scripts.e2e_server', url: 'http://127.0.0.1:8000/api/health', reuseExistingServer: false, timeout: 30000,
  },
});
