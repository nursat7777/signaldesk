import { useEffect, useState } from "react";
import { Activity, ArrowRight, Globe2, RefreshCw } from "lucide-react";
import { App } from "./App";
import type { AuthService } from "./api-service";
import { ServiceError } from "./service";
const copy = {
  en: {
    eyebrow: "AGENCY INTELLIGENCE",
    title: "Your campaigns.\nA clearer picture.",
    description:
      "Understand performance, compare channels and give every client a clear view of the results.",
    signin: "Sign in to your workspace",
    approved:
      "Access is limited to accounts approved by your agency administrator.",
    google: "Continue with Google",
    setup: "Google sign-in needs configuration",
    setupDetail:
      "Your administrator must configure the Google OAuth client and redirect URL on the server. Demo accounts are unavailable in this mode.",
    loading: "Checking your session…",
    retry: "Try again",
    forbidden:
      "This account does not have workspace access. Contact your agency administrator.",
    network:
      "Could not connect to the server. Check the backend connection and try again.",
    failed: "Sign-in could not be completed. Please try again.",
    logout: "Could not sign out. Please try again.",
    foot: "One agency. Every client. Full clarity.",
  },
  ru: {
    eyebrow: "АНАЛИТИКА АГЕНТСТВА",
    title: "Ваши кампании.\nЯсная картина.",
    description:
      "Анализируйте показатели, сравнивайте каналы и показывайте каждому клиенту результаты.",
    signin: "Войдите в рабочее пространство",
    approved:
      "Доступ открыт только аккаунтам, одобренным администратором агентства.",
    google: "Продолжить с Google",
    setup: "Необходимо настроить вход через Google",
    setupDetail:
      "Администратор должен указать OAuth-клиент Google и адрес перенаправления на сервере. Тестовые аккаунты в этом режиме недоступны.",
    loading: "Проверяем сессию…",
    retry: "Повторить",
    forbidden: "У аккаунта нет доступа. Обратитесь к администратору агентства.",
    network:
      "Не удалось подключиться к серверу. Проверьте подключение и повторите попытку.",
    failed: "Не удалось выполнить вход. Повторите попытку.",
    logout: "Не удалось выйти. Повторите попытку.",
    foot: "Одно агентство. Все клиенты. Полная ясность.",
  },
};
export function AuthGate({ api }: { api: AuthService }) {
  const [lang, setLang] = useState<"en" | "ru">(() =>
    localStorage.getItem("signaldesk-language") === "ru" ? "ru" : "en",
  );
  const [state, setState] = useState<
    "loading" | "ready" | "login" | "setup" | "error"
  >("loading");
  const [error, setError] = useState<
    "forbidden" | "network" | "failed" | "logout" | null
  >(null);
  const [attempt, setAttempt] = useState(0);
  const t = copy[lang];
  useEffect(() => {
    localStorage.setItem("signaldesk-language", lang);
    document.documentElement.lang = lang;
  }, [lang]);
  useEffect(() => {
    let active = true;
    setState("loading");
    setError(null);
    (async () => {
      try {
        await api.getMe();
        if (active) setState("ready");
      } catch (e) {
        if (!active) return;
        if (
          e instanceof ServiceError &&
          (e.code === "unauthorized" || e.code === "forbidden")
        ) {
          if (e.code === "forbidden") setError("forbidden");
          try {
            const status = await api.authStatus();
            if (active) setState(status.configured ? "login" : "setup");
          } catch {
            if (active) {
              setError("network");
              setState("error");
            }
          }
        } else {
          setError("network");
          setState("error");
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [api, attempt]);
  const logout = async () => {
    try {
      await api.logout();
      setAttempt((n) => n + 1);
    } catch {
      setError("logout");
    }
  };
  if (state === "ready")
    return (
      <>
        {error === "logout" && (
          <div role="alert" className="alert error">
            {t.logout}
            <button className="text-btn" onClick={logout}>
              {t.retry}
            </button>
          </div>
        )}
        <App api={api} demo={false} onLogout={logout} />
      </>
    );
  return (
    <div className="login-page">
      <header className="login-header">
        <div className="brand">
          <span className="brandmark">
            <Activity size={22} />
          </span>
          signaldesk<span className="branddot">®</span>
        </div>
        <button
          className="language"
          onClick={() => setLang((l) => (l === "en" ? "ru" : "en"))}
        >
          <Globe2 size={16} />
          {lang === "en" ? "Русский" : "English"}
        </button>
      </header>
      <main className="login-main">
        <section className="login-story">
          <div className="eyebrow">{t.eyebrow}</div>
          <h1>
            {t.title.split("\n").map((line, i) => (
              <span key={line}>
                {line}
                {i === 0 && <br />}
              </span>
            ))}
          </h1>
          <p>{t.description}</p>
          <div className="login-signal" aria-hidden="true">
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
            <i />
          </div>
          <small>{t.foot}</small>
        </section>
        <section className="login-card">
          <div className="eyebrow">SIGNALDESK / WORKSPACE</div>
          <h2>{t.signin}</h2>
          <p>{t.approved}</p>
          {state === "loading" ? (
            <div role="status" className="login-state">
              {t.loading}
            </div>
          ) : (
            <>
              {error && (
                <div role="alert" className="alert error">
                  {t[error]}
                </div>
              )}
              {state === "setup" ? (
                <div className="setup-state" role="status">
                  <strong>{t.setup}</strong>
                  <p>{t.setupDetail}</p>
                </div>
              ) : state === "login" ? (
                <a className="google-button" href={api.loginUrl}>
                  <span>G</span>
                  {t.google}
                  <ArrowRight size={17} />
                </a>
              ) : null}
              <button
                className="text-btn retry"
                onClick={() => setAttempt((n) => n + 1)}
              >
                <RefreshCw size={13} />
                {t.retry}
              </button>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
