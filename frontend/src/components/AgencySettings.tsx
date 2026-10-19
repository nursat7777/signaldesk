import { Plus } from "lucide-react";
import type { FormEvent, Dispatch, SetStateAction } from "react";
import type { User, Client, Service } from "../service";
import type { TextKey } from "../i18n";
type Modal = "metric" | "campaign" | "client" | "user" | null;
export function AgencySettings({
  t,
  clients,
  users,
  me,
  api,
  act,
  setError,
  setModal,
}: {
  t: (key: TextKey) => string;
  clients: Client[];
  users: User[];
  me: User;
  api: Service;
  act: (f: () => Promise<unknown>) => Promise<void>;
  setError: Dispatch<SetStateAction<string>>;
  setModal: Dispatch<SetStateAction<Modal>>;
}) {
  function formData(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    return new FormData(e.currentTarget);
  }
  return (
    <div className="settings-grid">
      <section className="panel">
        <div className="panel-head">
          <h2>{t("manageClients")}</h2>
          <button
            className="secondary"
            onClick={() => {
              setError("");
              setModal("client");
            }}
          >
            <Plus size={15} />
            {t("createClient")}
          </button>
        </div>
        {clients.map((c) => (
          <div className="client-row" key={c.id}>
            <span className="client-icon">{c.name.slice(0, 1)}</span>
            <div>
              <strong>{c.name}</strong>
              <small>
                {c.currency} · {t(c.archived ? "archived" : "active")}
              </small>
            </div>
            <button
              className="text-btn"
              onClick={() =>
                act(() => api.updateClient(c.id, { archived: !c.archived }))
              }
            >
              {t(c.archived ? "restore" : "archive")}
            </button>
          </div>
        ))}
      </section>
      <section className="panel">
        <div className="panel-head">
          <h2>{t("manageUsers")}</h2>
          <button
            className="secondary"
            onClick={() => {
              setError("");
              setModal("user");
            }}
          >
            <Plus size={15} />
            {t("createUser")}
          </button>
        </div>
        {users.map((u) => (
          <div className="user-row" key={u.id}>
            <div className="user-main">
              <span className="avatar">{u.name.slice(0, 1)}</span>
              <div>
                <strong>{u.name}</strong>
                <small>
                  {u.email} · {t(u.role)}
                </small>
              </div>
              {u.id !== me.id && (
                <button
                  className="text-btn"
                  onClick={() =>
                    act(() => api.updateUser(u.id, { enabled: !u.enabled }))
                  }
                >
                  {t(u.enabled ? "disable" : "enable")}
                </button>
              )}
            </div>
            {u.role === "marketer" && (
              <form
                className="assignments"
                onSubmit={(e) => {
                  const d = formData(e);
                  act(() =>
                    api.setAssignments(u.id, d.getAll("clientIds") as string[]),
                  );
                }}
              >
                <span>{t("assigned")}</span>
                {clients.map((c) => (
                  <label key={c.id}>
                    <input
                      name="clientIds"
                      type="checkbox"
                      value={c.id}
                      defaultChecked={u.clientIds.includes(c.id)}
                    />
                    {c.name}
                  </label>
                ))}
                <button className="secondary" type="submit">
                  {t("assign")}
                </button>
              </form>
            )}
          </div>
        ))}
      </section>
    </div>
  );
}
