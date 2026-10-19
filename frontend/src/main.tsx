import React from "react";
import { createRoot } from "react-dom/client";
import { AuthGate } from "./AuthGate";
import { createApiService } from "./api-service";
import "./style.css";
const root = createRoot(document.getElementById("root")!);
async function start() {
  if (import.meta.env.DEV && import.meta.env.VITE_SERVICE_MODE === "mock") {
    const [{ createMockService }, { App }] = await Promise.all([
      import("./service"),
      import("./App"),
    ]);
    const demo = createMockService();
    root.render(
      <React.StrictMode>
        <App api={demo.service} demo demoController={demo} />
      </React.StrictMode>,
    );
  } else
    root.render(
      <React.StrictMode>
        <AuthGate
          api={createApiService(import.meta.env.VITE_API_BASE || "/api")}
        />
      </React.StrictMode>,
    );
}
void start();
