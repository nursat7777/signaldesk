import { describe, it, expect, vi } from "vitest";
import { createApiService } from "./api-service";
import { today } from "./service";
const user = {
  id: "u",
  email: "a@b.com",
  name: "A",
  role: "admin",
  enabled: true,
  clientId: null,
  clientIds: [],
};
function harness() {
  const calls: { url: string; init: RequestInit }[] = [];
  const responses: Response[] = [];
  const fetcher = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    calls.push({ url: String(url), init: init || {} });
    return responses.shift() || new Response("{}", { status: 200 });
  });
  return {
    calls,
    responses,
    api: createApiService("/api", fetcher as typeof fetch),
  };
}
const ok = (body: unknown, headers?: HeadersInit) =>
  new Response(JSON.stringify(body), { status: 200, headers });
describe("REST adapter boundary", () => {
  it("uses cookie credentials and captured CSRF; maps campaign and metric money exactly", async () => {
    const { api, calls, responses } = harness();
    responses.push(ok(user, { "X-CSRF-Token": "session-csrf" }));
    await api.getMe();
    responses.push(
      ok({
        id: "p",
        clientId: "c /1",
        name: "Test",
        channel: "Other",
        archived: false,
      }),
    );
    await api.createCampaign({
      clientId: "c /1",
      name: "Test",
      channel: "Other",
    });
    expect(calls[1].url).toBe("/api/clients/c%20%2F1/campaigns");
    expect(JSON.parse(String(calls[1].init.body))).toEqual({
      name: "Test",
      channel: "Other",
    });
    expect(calls[1].init.credentials).toBe("include");
    expect(calls[1].init.headers).toMatchObject({
      "X-CSRF-Token": "session-csrf",
    });
    expect(calls[1].init.headers).not.toHaveProperty("Origin");
    const record = {
      id: "m",
      campaignId: "p",
      date: today(),
      spend: "10.25",
      impressions: 10,
      clicks: 3,
      leads: 2,
      sales: 1,
      revenue: "40.50",
      version: 2,
    };
    responses.push(ok(record));
    const result = await api.saveMetric({
      ...record,
      spend: 10.25,
      revenue: 40.5,
    });
    expect(result.spend).toBe(10.25);
    expect(result.revenue).toBe(40.5);
    const body = JSON.parse(String(calls[2].init.body));
    expect(body).toEqual({
      impressions: 10,
      clicks: 3,
      leads: 2,
      sales: 1,
      version: 2,
      spend: "10.25",
      revenue: "40.50",
    });
  });
  it("decodes metrics, query parameters, 204 assignments and logout", async () => {
    const { api, calls, responses } = harness();
    responses.push(
      ok([
        {
          id: "m",
          campaignId: "p",
          date: today(),
          spend: "0.25",
          impressions: 1,
          clicks: 1,
          leads: 0,
          sales: 0,
          revenue: "0.00",
          version: 1,
        },
      ]),
    );
    expect(
      (await api.listMetrics("c", "2026-01-01", "2026-02-01"))[0].spend,
    ).toBe(0.25);
    expect(calls[0].url).toContain("?from=2026-01-01&to=2026-02-01");
    responses.push(new Response(null, { status: 204 }));
    expect(await api.setAssignments("u", ["c"])).toBeUndefined();
    expect(JSON.parse(String(calls[1].init.body))).toEqual({
      clientIds: ["c"],
    });
    responses.push(new Response(null, { status: 204 }));
    await api.logout();
    expect(calls[2].url).toBe("/api/auth/logout");
  });
  it("maps structured errors and network failure without mock fallback; bounds reject before fetch", async () => {
    const { api, responses, calls } = harness();
    responses.push(
      new Response('{"code":"conflict","message":"stale"}', { status: 409 }),
    );
    await expect(api.listClients()).rejects.toMatchObject({ code: "conflict" });
    responses.push(new Response("gateway", { status: 401 }));
    await expect(api.getMe()).rejects.toMatchObject({ code: "unauthorized" });
    const data = {
      campaignId: "p",
      date: today(),
      spend: 1000000000000,
      impressions: 1,
      clicks: 1,
      leads: 0,
      sales: 0,
      revenue: 0,
    };
    await expect(api.saveMetric(data)).rejects.toMatchObject({
      code: "invalidNumber",
    });
    expect(calls).toHaveLength(2);
    const failing = createApiService(
      "/api",
      vi.fn().mockRejectedValue(new Error("offline")),
    );
    await expect(failing.getMe()).rejects.toMatchObject({ code: "network" });
  });

  it("accepts exact large two-decimal money through upper bound, rejects overflow and fractional counts", async () => {
    const { api, responses } = harness();
    const base = {
      campaignId: "p",
      date: today(),
      spend: 123456789012.35,
      impressions: 2147483647,
      clicks: 1,
      leads: 0,
      sales: 0,
      revenue: 999999999999.99,
    };
    responses.push(
      ok({
        ...base,
        id: "m",
        spend: "123456789012.35",
        revenue: "999999999999.99",
        version: 1,
      }),
    );
    expect((await api.saveMetric(base)).revenue).toBe(999999999999.99);
    for (const patch of [
      { spend: 1000000000000 },
      { impressions: 2147483648 },
      { clicks: 1.1 },
      { spend: 1.001 },
    ])
      await expect(api.saveMetric({ ...base, ...patch })).rejects.toMatchObject(
        { code: "invalidNumber" },
      );
  });
});
