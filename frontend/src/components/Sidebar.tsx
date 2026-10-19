import {
  Activity,
  ChevronDown,
  LayoutDashboard,
  Layers3,
  BarChart3,
  Settings2,
  Globe2,
} from "lucide-react";
import type { Dispatch, SetStateAction } from "react";
import type { User, Client } from "../service";
import type { TextKey } from "../i18n";
type Tab = "overview" | "campaigns" | "channels" | "team";
export function Sidebar({
  t,
  me,
  client,
  tab,
  setTab,
  lang,
  setLang,
}: {
  t: (key: TextKey) => string;
  me: User | null;
  client: Client | undefined;
  tab: Tab;
  setTab: Dispatch<SetStateAction<Tab>>;
  lang: "en" | "ru";
  setLang: Dispatch<SetStateAction<"en" | "ru">>;
}) {
  return (
    <aside className="sidebar">
      <a className="brand" href="#" aria-label="SignalDesk">
        <span className="brandmark">
          <Activity size={22} />
        </span>
        signaldesk<span className="branddot">®</span>
      </a>
      <div className="workspace">
        <span className="workspace-avatar">S</span>
        <div>
          <strong>Studio Agency</strong>
          <small>{t("workspace")}</small>
        </div>
        <ChevronDown size={14} />
      </div>
      <div className="nav-label">WORKSPACE</div>
      <nav>
        {(
          [
            "overview",
            "campaigns",
            "channels",
            ...(me?.role === "admin" ? ["team"] : []),
          ] as Tab[]
        ).map((k) => (
          <button
            key={k}
            className={tab === k ? "nav active" : "nav"}
            onClick={() => setTab(k)}
          >
            {k === "overview" ? (
              <LayoutDashboard size={18} />
            ) : k === "campaigns" ? (
              <Layers3 size={18} />
            ) : k === "channels" ? (
              <BarChart3 size={18} />
            ) : (
              <Settings2 size={18} />
            )}
            <span>{t(k)}</span>
            {tab === k && <span className="nav-dot" />}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="sidebar-note">
          <span className="live-dot" />
          {t("moneyNote")}
          <strong>{client?.currency || "—"}</strong>
          <small>{t("currencyNote")}</small>
        </div>
        <button
          className="language"
          onClick={() => setLang((l) => (l === "en" ? "ru" : "en"))}
        >
          <Globe2 size={16} />
          {lang === "en" ? "English" : "Русский"}
          <span>{lang === "en" ? "RU" : "EN"}</span>
        </button>
        <div className="profile">
          <span className="avatar">
            {me?.name?.slice(0, 2).toUpperCase() || "…"}
          </span>
          <div>
            <strong>{me?.name}</strong>
            <small>{me ? t(me.role) : t("loading")}</small>
          </div>
        </div>
      </div>
    </aside>
  );
}
