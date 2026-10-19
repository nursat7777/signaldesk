import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Command,
  Globe2,
  LayoutDashboard,
  Plus,
  Settings2,
  SlidersHorizontal,
  X,
  Users,
  Check,
  Layers3,
} from "lucide-react";
import {
  service as defaultService,
  mock,
  aggregate,
  channels,
  daysAgo,
  today,
  metricKeys,
  ServiceError,
  type Service,
  type User,
  type Client,
  type Campaign,
  type Metric,
  type MetricInput,
  type Currency,
  type Role,
} from "./service";
import { en, ru, type TextKey } from "./i18n";
import { Trend } from "./components/Trend";
import { Sidebar } from "./components/Sidebar";
import { AgencySettings } from "./components/AgencySettings";
type Tab = "overview" | "campaigns" | "channels" | "team";
type Modal = "metric" | "campaign" | "client" | "user" | null;
export function App({
  api = defaultService,
  demo = true,
}: {
  api?: Service;
  demo?: boolean;
}) {
  const [lang, setLang] = useState<"en" | "ru">(() =>
    localStorage.getItem("signaldesk-language") === "ru" ? "ru" : "en",
  );
  useEffect(() => {
    localStorage.setItem("signaldesk-language", lang);
    document.documentElement.lang = lang;
  }, [lang]);
  const t = (k: TextKey) => (lang === "en" ? en[k] : ru[k]);
  const [me, setMe] = useState<User | null>(null),
    [clients, setClients] = useState<Client[]>([]),
    [selected, setSelected] = useState(""),
    [campaigns, setCampaigns] = useState<Campaign[]>([]),
    [metrics, setMetrics] = useState<Metric[]>([]),
    [users, setUsers] = useState<User[]>([]),
    [tab, setTab] = useState<Tab>("overview"),
    [from, setFrom] = useState(daysAgo(29)),
    [to, setTo] = useState(today()),
    [modal, setModal] = useState<Modal>(null),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [loading, setLoading] = useState(true),
    [revision, setRevision] = useState(0),
    [query, setQuery] = useState("");
  const [currentCampaign, setCurrentCampaign] = useState(""),
    [entryDate, setEntryDate] = useState(today()),
    [values, setValues] = useState<Record<string, string>>({}),
    [version, setVersion] = useState<number | undefined>(),
    [saving, setSaving] = useState(false);
  const client = clients.find((c) => c.id === selected),
    canWrite = me?.role !== "client";
  const money = (n: number) =>
    new Intl.NumberFormat(lang === "en" ? "en-US" : "ru-RU", {
      style: "currency",
      currency: client?.currency || "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(n);
  const num = (n: number) =>
    new Intl.NumberFormat(lang === "en" ? "en-US" : "ru-RU", {
      maximumFractionDigits: 1,
    }).format(n);
  const fail = (e: unknown) =>
    setError(
      e instanceof ServiceError
        ? e.code === "archived"
          ? t("archivedError")
          : t(e.code in en ? (e.code as TextKey) : "error")
        : t("error"),
    );
  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([api.getMe(), api.listClients()])
      .then(([u, cs]) => {
        if (!active) return;
        setMe(u);
        setClients(cs);
        setSelected((s) => (cs.some((c) => c.id === s) ? s : cs[0]?.id || ""));
        if (u.role !== "admin") setTab((x) => (x === "team" ? "overview" : x));
      })
      .catch(fail)
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [api, revision]);
  useEffect(() => {
    let active = true;
    if (!selected) {
      setCampaigns([]);
      setMetrics([]);
      return;
    }
    setError("");
    if (from > to) {
      setError(t("dateRange"));
      return;
    }
    Promise.all([
      api.listCampaigns(selected),
      api.listMetrics(selected, from, to),
    ])
      .then(([ps, ms]) => {
        if (active) {
          setCampaigns(ps);
          setMetrics(ms);
        }
      })
      .catch(fail);
    return () => {
      active = false;
    };
  }, [api, selected, from, to, revision, lang]);
  useEffect(() => {
    if (me?.role === "admin") api.listUsers().then(setUsers).catch(fail);
  }, [api, me, revision]);
  useEffect(() => {
    if (modal !== "metric" || !currentCampaign) return;
    let active = true;
    api
      .listMetrics(selected, entryDate, entryDate)
      .then((rows) => {
        if (!active) return;
        const existing = rows.find((m) => m.campaignId === currentCampaign);
        setVersion(existing?.version);
        setValues(
          Object.fromEntries(
            metricKeys.map((k) => [k, existing ? String(existing[k]) : ""]),
          ),
        );
      })
      .catch(fail);
    return () => {
      active = false;
    };
  }, [api, modal, currentCampaign, entryDate, selected]);
  const act = async (f: () => Promise<unknown>) => {
    setError("");
    setNotice("");
    setSaving(true);
    try {
      await f();
      setModal(null);
      setRevision((r) => r + 1);
      setNotice(t("saved"));
    } catch (e) {
      fail(e);
    } finally {
      setSaving(false);
    }
  };
  const openMetric = (id?: string) => {
    setError("");
    setNotice("");
    setCurrentCampaign(id || campaigns.find((c) => !c.archived)?.id || "");
    setEntryDate(today());
    setModal("metric");
  };
  const close = () => {
    setModal(null);
    setError("");
  };
  const total = aggregate(metrics);
  const ratio = (n: number | null, suffix = "") =>
    n === null ? "—" : `${num(n)}${suffix}`;
  const filtered = campaigns.filter((p) =>
    p.name.toLowerCase().includes(query.toLowerCase()),
  );
  function field(label: ReactNode, child: ReactNode) {
    return (
      <label
        className="field"
        key={typeof label === "string" ? label : undefined}
      >
        <span>{label}</span>
        {child}
      </label>
    );
  }
  function formData(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    return new FormData(e.currentTarget);
  }
  return (
    <div className="app">
      <Sidebar
        t={t}
        me={me}
        client={client}
        tab={tab}
        setTab={setTab}
        lang={lang}
        setLang={setLang}
      />
      <main>
        <header className="topbar">
          <div className="breadcrumb">
            Studio Agency <ChevronRight size={14} />
            <span>{t(tab)}</span>
          </div>
          <div className="topbar-right">
            <span className="timezone">ALMATY · UTC+5</span>
            <span className="topbar-divider" />
            <span className="tiny-avatar">{me?.name?.slice(0, 1) || "S"}</span>
          </div>
        </header>
        {demo && (
          <div className="demo-banner">
            <span>{t("demo")}</span>
            <label>
              {t("demoHint")}
              <select
                aria-label={t("demoHint")}
                value={me?.id || "u1"}
                onChange={(e) => {
                  mock.setIdentity(e.target.value);
                  setSelected("");
                  setRevision((r) => r + 1);
                }}
              >
                {mock
                  .identities()
                  .filter((u) => u.enabled)
                  .map((u) => (
                    <option value={u.id} key={u.id}>
                      {u.name} · {t(u.role)}
                    </option>
                  ))}
              </select>
            </label>
            <span className="demo-tooltip" title={t("demoNotice")}>
              ⓘ
            </span>
          </div>
        )}
        <div className="content">
          <section className="page-heading">
            <div className="eyebrow">
              {tab === "team"
                ? "CONTROL CENTER"
                : "ANALYTICS / " + (client?.currency || "—")}
            </div>
            <div className="heading-row">
              <div>
                <h1>{tab === "overview" ? t("intelligence") : t(tab)}</h1>
                <p>{tab === "team" ? t("settingsSub") : t("subtitle")}</p>
              </div>
              {tab !== "team" && canWrite && client && !client.archived && (
                <button
                  className="primary"
                  onClick={() => openMetric()}
                  disabled={!campaigns.some((c) => !c.archived)}
                >
                  <Plus size={17} />
                  {t("entry")}
                </button>
              )}
            </div>
          </section>
          {error && (
            <div role="alert" className="alert error">
              {error}
            </div>
          )}
          {notice && (
            <div role="status" className="alert success">
              <Check size={16} />
              {notice}
            </div>
          )}
          {loading ? (
            <div className="empty">{t("loading")}</div>
          ) : tab === "team" && me?.role === "admin" ? (
            <>
              <AgencySettings
                t={t}
                clients={clients}
                users={users}
                me={me}
                api={api}
                act={act}
                setError={setError}
                setModal={setModal}
              />
            </>
          ) : !client ? (
            <div className="empty">
              <Users size={32} />
              <h2>{t("noClients")}</h2>
              <p>{t("noClientsSub")}</p>
            </div>
          ) : (
            <>
              <div className="filters">
                <label className="client-select">
                  <span className="client-icon">{client.name.slice(0, 1)}</span>
                  <select
                    aria-label={t("clients")}
                    value={selected}
                    onChange={(e) => setSelected(e.target.value)}
                  >
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name}
                        {c.archived ? ` (${t("archived")})` : ""}
                      </option>
                    ))}
                  </select>
                  <span className="currency-badge">{client.currency}</span>
                </label>
                <div className="date-filters">
                  <SlidersHorizontal size={15} />
                  {field(
                    t("from"),
                    <input
                      type="date"
                      aria-label={t("from")}
                      value={from}
                      onChange={(e) => setFrom(e.target.value)}
                    />,
                  )}
                  <span className="date-dash">—</span>
                  {field(
                    t("to"),
                    <input
                      type="date"
                      aria-label={t("to")}
                      value={to}
                      onChange={(e) => setTo(e.target.value)}
                    />,
                  )}
                  <button
                    className="icon-button"
                    title={t("latest")}
                    aria-label={t("latest")}
                    onClick={() => {
                      setFrom(daysAgo(29));
                      setTo(today());
                    }}
                  >
                    ↺
                  </button>
                </div>
              </div>
              {tab === "overview" && (
                <>
                  <div className="kpi-grid">
                    {(["spend", "revenue", "leads", "roas"] as const).map(
                      (k, i) => (
                        <article
                          className={"kpi " + (k === "roas" ? "highlight" : "")}
                          key={k}
                        >
                          <div className="kpi-label">
                            {t(k)}
                            <span>
                              {i < 2 ? (
                                <ArrowUpRight size={16} />
                              ) : i === 2 ? (
                                <Users size={16} />
                              ) : (
                                <Activity size={16} />
                              )}
                            </span>
                          </div>
                          <div className="kpi-value">
                            {k === "spend" || k === "revenue"
                              ? money(total[k])
                              : k === "roas"
                                ? ratio(total[k], "×")
                                : num(total[k])}
                          </div>
                          <div className="kpi-foot">
                            {k === "roas"
                              ? t("roas")
                              : `${metrics.length} ${t("records")}`}
                          </div>
                        </article>
                      ),
                    )}
                  </div>
                  <section className="panel chart-panel">
                    <div className="panel-head">
                      <div>
                        <h2>{t("trend")}</h2>
                        <p>{t("trendSub")}</p>
                      </div>
                      <div className="legend">
                        <span>
                          <i className="lime" />
                          {t("revenue")}
                        </span>
                        <span>
                          <i className="cyan" />
                          {t("spend")}
                        </span>
                      </div>
                    </div>
                    <Trend
                      metrics={metrics}
                      from={from}
                      to={to}
                      labels={{
                        empty: t("noData"),
                        revenue: t("revenue"),
                        spend: t("spend"),
                      }}
                      format={money}
                    />
                  </section>
                  <div className="secondary-kpis">
                    {(
                      [
                        "impressions",
                        "clicks",
                        "sales",
                        "ctr",
                        "cpc",
                        "cpl",
                      ] as const
                    ).map((k) => (
                      <div key={k}>
                        <span>{t(k)}</span>
                        <strong>
                          {k === "cpc" || k === "cpl"
                            ? total[k] === null
                              ? "—"
                              : money(total[k])
                            : k === "ctr"
                              ? ratio(total[k], "%")
                              : num(total[k])}
                        </strong>
                      </div>
                    ))}
                  </div>
                </>
              )}
              {tab === "channels" ? (
                <section className="panel">
                  <div className="panel-head">
                    <div>
                      <h2>{t("comparison")}</h2>
                      <p>{t("comparisonSub")}</p>
                    </div>
                  </div>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>{t("channel")}</th>
                          {(
                            [
                              "spend",
                              "revenue",
                              "leads",
                              "ctr",
                              "cpc",
                              "cpl",
                              "roas",
                            ] as const
                          ).map((k) => (
                            <th key={k}>{t(k)}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {channels.map((ch, i) => {
                          const a = aggregate(
                            metrics.filter((m) =>
                              campaigns.some(
                                (p) =>
                                  p.id === m.campaignId && p.channel === ch,
                              ),
                            ),
                          );
                          return (
                            <tr key={ch}>
                              <td>
                                <span className={"channel-icon channel-" + i}>
                                  {ch.slice(0, 1)}
                                </span>
                                {ch}
                              </td>
                              <td>{money(a.spend)}</td>
                              <td>{money(a.revenue)}</td>
                              <td>{num(a.leads)}</td>
                              <td>{ratio(a.ctr, "%")}</td>
                              <td>{a.cpc === null ? "—" : money(a.cpc)}</td>
                              <td>{a.cpl === null ? "—" : money(a.cpl)}</td>
                              <td className="lime-text">
                                {ratio(a.roas, "×")}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </section>
              ) : (
                <section className="panel campaign-panel">
                  <div className="panel-head">
                    <div>
                      <h2>
                        {t("campaigns")}{" "}
                        <span className="count">{campaigns.length}</span>
                      </h2>
                      <p>
                        {client.name} <span className="muted-dot">·</span>{" "}
                        {from} — {to}
                      </p>
                    </div>
                    <div className="table-actions">
                      {tab === "campaigns" && (
                        <input
                          className="search-input"
                          aria-label={t("search")}
                          placeholder={t("search")}
                          value={query}
                          onChange={(e) => setQuery(e.target.value)}
                        />
                      )}{" "}
                      {canWrite && !client.archived && (
                        <button
                          className="secondary"
                          onClick={() => {
                            setError("");
                            setModal("campaign");
                          }}
                        >
                          <Plus size={15} />
                          {t("newCampaign")}
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>{t("campaign")}</th>
                          <th>{t("status")}</th>
                          <th>{t("spend")}</th>
                          <th>{t("revenue")}</th>
                          <th>{t("leads")}</th>
                          <th>ROAS</th>
                          {canWrite && (
                            <th>
                              <span className="sr-only">{t("edit")}</span>
                            </th>
                          )}
                        </tr>
                      </thead>
                      <tbody>
                        {filtered.map((p) => {
                          const a = aggregate(
                            metrics.filter((m) => m.campaignId === p.id),
                          );
                          return (
                            <tr key={p.id}>
                              <td>
                                <div className="campaign-name">
                                  <span
                                    className={
                                      "channel-icon channel-" +
                                      channels.indexOf(p.channel)
                                    }
                                  >
                                    {p.channel[0]}
                                  </span>
                                  <div>
                                    <strong>{p.name}</strong>
                                    <small>{p.channel}</small>
                                  </div>
                                </div>
                              </td>
                              <td>
                                <span
                                  className={
                                    "status " + (p.archived ? "off" : "")
                                  }
                                >
                                  <i />
                                  {t(p.archived ? "archived" : "active")}
                                </span>
                              </td>
                              <td>{money(a.spend)}</td>
                              <td>{money(a.revenue)}</td>
                              <td>{num(a.leads)}</td>
                              <td className="lime-text">
                                {ratio(a.roas, "×")}
                              </td>
                              {canWrite && (
                                <td>
                                  <div className="row-actions">
                                    <button
                                      className="text-btn"
                                      disabled={p.archived || client.archived}
                                      onClick={() => openMetric(p.id)}
                                    >
                                      {t("edit")}
                                    </button>
                                    <button
                                      className="text-btn muted"
                                      onClick={() =>
                                        act(() =>
                                          api.updateCampaign(p.id, {
                                            archived: !p.archived,
                                          }),
                                        )
                                      }
                                    >
                                      {t(p.archived ? "restore" : "archive")}
                                    </button>
                                  </div>
                                </td>
                              )}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                    {!filtered.length && (
                      <div className="empty">
                        <Layers3 size={28} />
                        <h3>{t("emptyCampaigns")}</h3>
                        <p>{t("emptyCampaignsSub")}</p>
                      </div>
                    )}
                  </div>
                  <div className="table-footer">
                    <span>
                      {metrics.length} {t("records")}
                    </span>
                    <span>
                      {t("moneyNote")}: <strong>{client.currency}</strong>
                    </span>
                  </div>
                </section>
              )}
            </>
          )}
        </div>
        <footer>
          SignalDesk <span>·</span> Agency intelligence{" "}
          <span className="footer-right">
            {canWrite ? "● " + t("enabled") : t("permission")}
          </span>
        </footer>
      </main>
      {modal && (
        <div
          className="modal-backdrop"
          onMouseDown={(e) => e.target === e.currentTarget && close()}
        >
          <section
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="modal-title"
          >
            <div className="modal-heading">
              <div>
                <div className="eyebrow">SIGNALDESK / {client?.currency}</div>
                <h2 id="modal-title">
                  {t(
                    modal === "metric"
                      ? "daily"
                      : modal === "campaign"
                        ? "newCampaign"
                        : modal === "client"
                          ? "createClient"
                          : "createUser",
                  )}
                </h2>
              </div>
              <button
                className="icon-button"
                aria-label={t("close")}
                onClick={close}
              >
                <X size={19} />
              </button>
            </div>
            {error && (
              <div role="alert" className="alert error">
                {error}
              </div>
            )}
            {modal === "metric" ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (
                    metricKeys.some(
                      (k) => values[k] === undefined || values[k].trim() === "",
                    )
                  ) {
                    setError(t("required"));
                    return;
                  }
                  const input = {
                    campaignId: currentCampaign,
                    date: entryDate,
                    ...Object.fromEntries(
                      metricKeys.map((k) => [k, Number(values[k])]),
                    ),
                    ...(version !== undefined ? { version } : {}),
                  } as MetricInput;
                  act(() => api.saveMetric(input));
                }}
              >
                <p className="modal-subtitle">{t("dailySub")}</p>
                <div className="form-grid">
                  {field(
                    t("campaign"),
                    <select
                      aria-label={t("campaign")}
                      required
                      value={currentCampaign}
                      onChange={(e) => setCurrentCampaign(e.target.value)}
                    >
                      <option value="">—</option>
                      {campaigns
                        .filter((c) => !c.archived)
                        .map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                    </select>,
                  )}
                  {field(
                    t("date"),
                    <input
                      aria-label={t("date")}
                      type="date"
                      required
                      max={today()}
                      value={entryDate}
                      onChange={(e) => setEntryDate(e.target.value)}
                    />,
                  )}
                </div>
                <div className="record-hint">
                  {version !== undefined ? (
                    <Check size={15} />
                  ) : (
                    <Plus size={15} />
                  )}{" "}
                  {t(version !== undefined ? "existing" : "newRecord")}
                </div>
                <div className="form-grid">
                  {metricKeys.map((k) =>
                    field(
                      t(k) +
                        (k === "spend" || k === "revenue"
                          ? ` (${client?.currency})`
                          : ""),
                      <input
                        key={k}
                        aria-label={t(k)}
                        type="number"
                        min="0"
                        step={k === "spend" || k === "revenue" ? "0.01" : "1"}
                        required
                        value={values[k] ?? ""}
                        onChange={(e) =>
                          setValues((v) => ({ ...v, [k]: e.target.value }))
                        }
                      />,
                    ),
                  )}
                </div>
                <div className="modal-actions">
                  <button type="button" className="secondary" onClick={close}>
                    {t("cancel")}
                  </button>
                  <button
                    className="primary"
                    disabled={saving || !currentCampaign}
                  >
                    {t("save")}
                  </button>
                </div>
              </form>
            ) : modal === "campaign" ? (
              <form
                onSubmit={(e) => {
                  const d = formData(e);
                  act(() =>
                    api.createCampaign({
                      clientId: selected,
                      name: String(d.get("name")),
                      channel: String(
                        d.get("channel"),
                      ) as (typeof channels)[number],
                    }),
                  );
                }}
              >
                {field(
                  t("name"),
                  <input
                    name="name"
                    aria-label={t("name")}
                    maxLength={120}
                    required
                    autoFocus
                  />,
                )}
                {field(
                  t("channel"),
                  <select name="channel" aria-label={t("channel")}>
                    {channels.map((ch) => (
                      <option key={ch}>{ch}</option>
                    ))}
                  </select>,
                )}
                <div className="modal-actions">
                  <button type="button" className="secondary" onClick={close}>
                    {t("cancel")}
                  </button>
                  <button className="primary" disabled={saving}>
                    {t("save")}
                  </button>
                </div>
              </form>
            ) : modal === "client" ? (
              <form
                onSubmit={(e) => {
                  const d = formData(e);
                  act(() =>
                    api.createClient({
                      name: String(d.get("name")),
                      currency: String(d.get("currency")) as Currency,
                    }),
                  );
                }}
              >
                {field(
                  t("name"),
                  <input
                    name="name"
                    aria-label={t("name")}
                    maxLength={120}
                    required
                    autoFocus
                  />,
                )}
                {field(
                  t("currency"),
                  <select name="currency" aria-label={t("currency")}>
                    {["KZT", "USD", "EUR"].map((c) => (
                      <option key={c}>{c}</option>
                    ))}
                  </select>,
                )}
                <div className="modal-actions">
                  <button type="button" className="secondary" onClick={close}>
                    {t("cancel")}
                  </button>
                  <button className="primary" disabled={saving}>
                    {t("save")}
                  </button>
                </div>
              </form>
            ) : (
              <form
                onSubmit={(e) => {
                  const d = formData(e);
                  act(() =>
                    api.createUser({
                      name: String(d.get("name")),
                      email: String(d.get("email")),
                      role: String(d.get("role")) as Role,
                      clientId: d.get("clientId")
                        ? String(d.get("clientId"))
                        : null,
                    }),
                  );
                }}
              >
                {field(
                  t("name"),
                  <input
                    name="name"
                    aria-label={t("name")}
                    required
                    autoFocus
                  />,
                )}
                {field(
                  t("email"),
                  <input
                    name="email"
                    aria-label={t("email")}
                    type="email"
                    required
                  />,
                )}
                {field(
                  t("role"),
                  <select
                    name="role"
                    aria-label={t("role")}
                    defaultValue="marketer"
                  >
                    {(["marketer", "client", "admin"] as Role[]).map((r) => (
                      <option key={r} value={r}>
                        {t(r)}
                      </option>
                    ))}
                  </select>,
                )}
                {field(
                  t("client"),
                  <select name="clientId" aria-label={t("client")}>
                    <option value="">—</option>
                    {clients.map((c) => (
                      <option value={c.id} key={c.id}>
                        {c.name}
                      </option>
                    ))}
                  </select>,
                )}
                <div className="modal-actions">
                  <button type="button" className="secondary" onClick={close}>
                    {t("cancel")}
                  </button>
                  <button className="primary" disabled={saving}>
                    {t("save")}
                  </button>
                </div>
              </form>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
