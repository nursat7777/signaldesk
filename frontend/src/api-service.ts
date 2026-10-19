import {
  ServiceError,
  validateMetric,
  type Service,
  type Metric,
  type MetricInput,
} from "./service";
type WireMetric = Omit<Metric, "spend" | "revenue"> & {
  spend: string;
  revenue: string;
};
export type AuthService = Service & {
  authStatus(): Promise<{ configured: boolean }>;
  logout(): Promise<void>;
  loginUrl: string;
};
export function createApiService(
  base = "/api",
  fetcher: typeof fetch = fetch,
): AuthService {
  let csrf: string | undefined;
  async function request<T>(
    path: string,
    method = "GET",
    body?: unknown,
  ): Promise<T> {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (method !== "GET" && csrf) headers["X-CSRF-Token"] = csrf;
    let response: Response;
    try {
      response = await fetcher(`${base}${path}`, {
        method,
        credentials: "include",
        headers,
        ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
      });
    } catch {
      throw new ServiceError("network");
    }
    const token = response.headers.get("X-CSRF-Token");
    if (token) csrf = token;
    if (!response.ok) {
      let code =
        response.status === 401
          ? "unauthorized"
          : response.status === 403
            ? "forbidden"
            : "error";
      try {
        const data = await response.json();
        if (typeof data.code === "string") code = data.code;
      } catch {
        /* non-JSON proxy failure retains status code */
      }
      throw new ServiceError(code);
    }
    if (response.status === 204) return undefined as T;
    return response.json() as Promise<T>;
  }
  const segment = (id: string) => encodeURIComponent(id);
  const decode = (m: WireMetric): Metric => ({
    ...m,
    spend: Number(m.spend),
    revenue: Number(m.revenue),
  });
  return {
    getMe: () => request("/me"),
    listClients: () => request("/clients"),
    createClient: (data) => request("/clients", "POST", data),
    updateClient: (id, data) =>
      request(`/clients/${segment(id)}`, "PATCH", data),
    listCampaigns: (id) => request(`/clients/${segment(id)}/campaigns`),
    createCampaign: ({ clientId, ...data }) =>
      request(`/clients/${segment(clientId)}/campaigns`, "POST", data),
    updateCampaign: (id, data) =>
      request(`/campaigns/${segment(id)}`, "PATCH", data),
    listMetrics: async (id, from, to) =>
      (
        await request<WireMetric[]>(
          `/clients/${segment(id)}/metrics?${new URLSearchParams({ from, to })}`,
        )
      ).map(decode),
    saveMetric: async (data: MetricInput) => {
      validateMetric(data);
      const {
        campaignId,
        date,
        spend,
        revenue,
        impressions,
        clicks,
        leads,
        sales,
        version,
      } = data;
      const rest = {
        impressions,
        clicks,
        leads,
        sales,
        ...(version !== undefined ? { version } : {}),
      };
      return decode(
        await request<WireMetric>(
          `/campaigns/${segment(campaignId)}/metrics/${segment(date)}`,
          "PUT",
          { ...rest, spend: spend.toFixed(2), revenue: revenue.toFixed(2) },
        ),
      );
    },
    listUsers: () => request("/users"),
    createUser: (data) => request("/users", "POST", data),
    updateUser: (id, data) => request(`/users/${segment(id)}`, "PATCH", data),
    setAssignments: (id, clientIds) =>
      request(`/users/${segment(id)}/assignments`, "PUT", { clientIds }),
    authStatus: () => request("/auth/status"),
    logout: async () => {
      await request("/auth/logout", "POST");
      csrf = undefined;
    },
    loginUrl: `${base}/auth/google`,
  };
}
