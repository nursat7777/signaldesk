export type Role = "admin" | "marketer" | "client";
export type Currency = "KZT" | "USD" | "EUR";
export const channels = [
  "Google Ads",
  "Meta Ads",
  "TikTok Ads",
  "Other",
] as const;
export type Channel = (typeof channels)[number];
export interface User {
  id: string;
  email: string;
  name: string;
  role: Role;
  enabled: boolean;
  clientId: string | null;
  clientIds: string[];
}
export interface Client {
  id: string;
  name: string;
  currency: Currency;
  archived: boolean;
}
export interface Campaign {
  id: string;
  clientId: string;
  name: string;
  channel: Channel;
  archived: boolean;
}
export interface Metric {
  id: string;
  campaignId: string;
  date: string;
  spend: number;
  impressions: number;
  clicks: number;
  leads: number;
  sales: number;
  revenue: number;
  version: number;
}
export type MetricInput = Omit<Metric, "id" | "version"> & { version?: number };
export const metricKeys = [
  "spend",
  "impressions",
  "clicks",
  "leads",
  "sales",
  "revenue",
] as const;
export class ServiceError extends Error {
  constructor(public code: string) {
    super(code);
  }
}
export const today = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Almaty",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date());
export function daysAgo(n: number) {
  const d = new Date(`${today()}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() - n);
  return d.toISOString().slice(0, 10);
}
export function aggregate(rows: Metric[]) {
  const total = {
    spend: 0,
    impressions: 0,
    clicks: 0,
    leads: 0,
    sales: 0,
    revenue: 0,
  };
  rows.forEach((r) => metricKeys.forEach((k) => (total[k] += r[k])));
  return {
    ...total,
    ctr: total.impressions ? (total.clicks / total.impressions) * 100 : null,
    cpc: total.clicks ? total.spend / total.clicks : null,
    cpl: total.leads ? total.spend / total.leads : null,
    roas: total.spend ? total.revenue / total.spend : null,
  };
}
export function validateMetric(m: MetricInput) {
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(m.date) ||
    Number.isNaN(Date.parse(m.date)) ||
    new Date(m.date).toISOString().slice(0, 10) !== m.date
  )
    throw new ServiceError("invalidDate");
  if (m.date > today()) throw new ServiceError("futureDate");
  metricKeys.forEach((k) => {
    if (
      !Number.isFinite(m[k]) ||
      m[k] < 0 ||
      (!["spend", "revenue"].includes(k) && !Number.isInteger(m[k])) ||
      (["spend", "revenue"].includes(k) &&
        Math.abs(m[k] * 100 - Math.round(m[k] * 100)) > 0.00001)
    )
      throw new ServiceError("invalidNumber");
  });
}
export interface Service {
  getMe(): Promise<User>;
  listClients(): Promise<Client[]>;
  createClient(data: Pick<Client, "name" | "currency">): Promise<Client>;
  updateClient(
    id: string,
    data: Partial<Pick<Client, "name" | "currency" | "archived">>,
  ): Promise<Client>;
  listCampaigns(clientId: string): Promise<Campaign[]>;
  createCampaign(data: Omit<Campaign, "id" | "archived">): Promise<Campaign>;
  updateCampaign(
    id: string,
    data: Partial<Pick<Campaign, "name" | "archived">>,
  ): Promise<Campaign>;
  listMetrics(clientId: string, from: string, to: string): Promise<Metric[]>;
  saveMetric(data: MetricInput): Promise<Metric>;
  listUsers(): Promise<User[]>;
  createUser(
    data: Pick<User, "name" | "email" | "role" | "clientId">,
  ): Promise<User>;
  updateUser(
    id: string,
    data: Partial<Pick<User, "enabled" | "role" | "clientId">>,
  ): Promise<User>;
  setAssignments(userId: string, clientIds: string[]): Promise<void>;
}
export function createMockService() {
  let seq = 100;
  let users: User[] = [
    {
      id: "u1",
      email: "admin@signaldesk.demo",
      name: "Alex Morgan",
      role: "admin",
      enabled: true,
      clientId: null,
      clientIds: [],
    },
    {
      id: "u2",
      email: "marketer@signaldesk.demo",
      name: "Dana Kim",
      role: "marketer",
      enabled: true,
      clientId: null,
      clientIds: ["c1", "c2"],
    },
    {
      id: "u3",
      email: "client@signaldesk.demo",
      name: "Aigerim S.",
      role: "client",
      enabled: true,
      clientId: "c1",
      clientIds: [],
    },
  ];
  let identity = "u1";
  const clients: Client[] = [
    { id: "c1", name: "Nomad Coffee", currency: "KZT", archived: false },
    { id: "c2", name: "Forma Studio", currency: "USD", archived: false },
    { id: "c3", name: "Nord Objects", currency: "EUR", archived: false },
  ];
  const campaigns: Campaign[] = clients.flatMap((c, i) =>
    channels.slice(0, 3).map((channel, j) => ({
      id: `p${i * 3 + j + 1}`,
      clientId: c.id,
      name: [
        "Search · Always on",
        "Social · New collection",
        "Video · Discovery",
      ][j],
      channel,
      archived: false,
    })),
  );
  const metrics: Metric[] = campaigns.flatMap((p, i) =>
    Array.from({ length: 30 }, (_, d) => {
      const scale = p.clientId === "c1" ? 470 : 1;
      const spend =
        Math.round((35 + ((d * 7 + i * 13) % 60)) * scale * 100) / 100;
      return {
        id: `m${i}-${d}`,
        campaignId: p.id,
        date: daysAgo(d),
        spend,
        impressions: 4200 + ((d * 179 + i * 953) % 9000),
        clicks: 150 + ((d * 13 + i * 41) % 350),
        leads: 8 + ((d * 3 + i * 5) % 32),
        sales: 2 + ((d + i) % 10),
        revenue: Math.round(spend * (2.1 + ((d + i) % 8) / 4) * 100) / 100,
        version: 1,
      };
    }),
  );
  const clone = <T>(x: T): T => structuredClone(x);
  const me = () => {
    const u = users.find((u) => u.id === identity);
    if (!u?.enabled) throw new ServiceError("forbidden");
    return u;
  };
  const admin = () => {
    if (me().role !== "admin") throw new ServiceError("forbidden");
  };
  const access = (id: string, write = false) => {
    const u = me();
    if (
      (u.role === "client" && (write || u.clientId !== id)) ||
      (u.role === "marketer" && !u.clientIds.includes(id))
    )
      throw new ServiceError("forbidden");
    if (!clients.some((c) => c.id === id)) throw new ServiceError("notFound");
  };
  const asyncCall = async <T>(f: () => T) => {
    await Promise.resolve();
    return clone(f());
  };
  const nonempty = (s: string) => {
    if (!s.trim()) throw new ServiceError("required");
  };
  const service: Service = {
    getMe: () => asyncCall(me),
    listClients: () =>
      asyncCall(() =>
        clients.filter((c) => {
          const u = me();
          return (
            u.role === "admin" ||
            (u.role === "marketer" && u.clientIds.includes(c.id)) ||
            (u.role === "client" && u.clientId === c.id)
          );
        }),
      ),
    createClient: (data) =>
      asyncCall(() => {
        admin();
        nonempty(data.name);
        const c = {
          ...data,
          name: data.name.trim(),
          id: `c${++seq}`,
          archived: false,
        };
        clients.push(c);
        return c;
      }),
    updateClient: (id, data) =>
      asyncCall(() => {
        admin();
        const c = clients.find((c) => c.id === id);
        if (!c) throw new ServiceError("notFound");
        if (
          data.currency &&
          data.currency !== c.currency &&
          metrics.some((m) =>
            campaigns.some((p) => p.id === m.campaignId && p.clientId === id),
          )
        )
          throw new ServiceError("currencyLocked");
        if (data.name !== undefined) nonempty(data.name);
        Object.assign(c, data);
        return c;
      }),
    listCampaigns: (id) =>
      asyncCall(() => {
        access(id);
        return campaigns.filter((p) => p.clientId === id);
      }),
    createCampaign: (data) =>
      asyncCall(() => {
        access(data.clientId, true);
        if (clients.find((c) => c.id === data.clientId)?.archived)
          throw new ServiceError("archived");
        nonempty(data.name);
        const p = {
          ...data,
          name: data.name.trim(),
          id: `p${++seq}`,
          archived: false,
        };
        campaigns.push(p);
        return p;
      }),
    updateCampaign: (id, data) =>
      asyncCall(() => {
        const p = campaigns.find((p) => p.id === id);
        if (!p) throw new ServiceError("notFound");
        access(p.clientId, true);
        if (data.name !== undefined) nonempty(data.name);
        Object.assign(p, data);
        return p;
      }),
    listMetrics: (id, from, to) =>
      asyncCall(() => {
        access(id);
        if (from > to) throw new ServiceError("dateRange");
        return metrics.filter(
          (m) =>
            campaigns.some((p) => p.id === m.campaignId && p.clientId === id) &&
            m.date >= from &&
            m.date <= to,
        );
      }),
    saveMetric: (data) =>
      asyncCall(() => {
        const p = campaigns.find((p) => p.id === data.campaignId);
        if (!p) throw new ServiceError("notFound");
        access(p.clientId, true);
        if (p.archived || clients.find((c) => c.id === p.clientId)?.archived)
          throw new ServiceError("archived");
        validateMetric(data);
        const old = metrics.find(
          (m) => m.campaignId === p.id && m.date === data.date,
        );
        if (old) {
          if (data.version !== old.version) throw new ServiceError("conflict");
          Object.assign(old, data, { version: old.version + 1 });
          return old;
        }
        if (data.version !== undefined) throw new ServiceError("conflict");
        const m = { ...data, id: `m${++seq}`, version: 1 };
        metrics.push(m);
        return m;
      }),
    listUsers: () =>
      asyncCall(() => {
        admin();
        return users;
      }),
    createUser: (data) =>
      asyncCall(() => {
        admin();
        nonempty(data.name);
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email))
          throw new ServiceError("invalidEmail");
        if (
          users.some((u) => u.email.toLowerCase() === data.email.toLowerCase())
        )
          throw new ServiceError("duplicateEmail");
        if (
          data.role === "client" &&
          !clients.some((c) => c.id === data.clientId)
        )
          throw new ServiceError("required");
        const u = {
          ...data,
          email: data.email.toLowerCase(),
          clientId: data.role === "client" ? data.clientId : null,
          id: `u${++seq}`,
          enabled: true,
          clientIds: [],
        };
        users.push(u);
        return u;
      }),
    updateUser: (id, data) =>
      asyncCall(() => {
        admin();
        if (id === identity) throw new ServiceError("selfDisable");
        const u = users.find((u) => u.id === id);
        if (!u) throw new ServiceError("notFound");
        const next = { ...u, ...data };
        if (
          next.role === "client" &&
          !clients.some((c) => c.id === next.clientId)
        )
          throw new ServiceError("required");
        if (next.role !== "client") next.clientId = null;
        if (next.role !== "marketer" || u.role !== "marketer")
          next.clientIds = [];
        Object.assign(u, next);
        return u;
      }),
    setAssignments: (id, ids) =>
      asyncCall(() => {
        admin();
        const u = users.find((u) => u.id === id);
        if (
          !u ||
          u.role !== "marketer" ||
          ids.some((id) => !clients.some((c) => c.id === id))
        )
          throw new ServiceError("invalidAssignment");
        u.clientIds = [...new Set(ids)];
      }),
  };
  return {
    service,
    setIdentity: (id: string) => {
      identity = id;
    },
    identities: () => clone(users),
  };
}
export const mock = createMockService();
export const service = mock.service;
