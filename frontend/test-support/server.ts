/** Isolated test infrastructure. Never imported by production application code. */
import { execFileSync, spawn, type ChildProcess } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { createServer } from "node:net";
import { request as httpRequest } from "node:http";
import { once } from "node:events";
import { createApiService } from "../src/api-service";
export type Actor = "admin" | "marketer" | "client";
interface Seed {
  sessions: Record<Actor, { cookie: string; csrf: string; userId: string }>;
  clientId: string;
  otherClientId: string;
  origin: string;
}
async function freePort() {
  const s = createServer();
  s.listen(0, "127.0.0.1");
  await once(s, "listening");
  const address = s.address();
  if (!address || typeof address === "string") throw new Error("No free port");
  const port = address.port;
  await new Promise<void>((r, j) => s.close((e) => (e ? j(e) : r())));
  return port;
}
async function waitReady(child: ChildProcess) {
  return new Promise<void>((resolveReady, reject) => {
    let logs = "";
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error("HTTP fixture startup timeout: " + logs));
    }, 15000);
    const fail = (code: number | null) => {
      clearTimeout(timer);
      reject(new Error("HTTP fixture exited " + code + ": " + logs));
    };
    child.once("exit", fail);
    child.once("error", (e) => {
      clearTimeout(timer);
      reject(e);
    });
    const read = (data: Buffer) => {
      logs += data.toString();
      if (logs.includes("Uvicorn running on")) {
        clearTimeout(timer);
        child.removeListener("exit", fail);
        resolveReady();
      }
    };
    child.stderr?.on("data", read);
    child.stdout?.on("data", read);
  });
}
export async function startHttpFixture() {
  const directory = mkdtempSync(resolve(tmpdir(), "signaldesk-http-"));
  const repo = resolve(process.cwd(), "..");
  const python = resolve(repo, ".venv/bin/python");
  const env = {
    ...process.env,
    DATABASE_URL: `sqlite:///${directory}/fixture.sqlite3`,
    BOOTSTRAP_ADMIN_EMAIL: "admin@fixture.test",
    FRONTEND_URL: "http://localhost:5173",
    ALLOWED_ORIGINS: "http://localhost:5173",
    GOOGLE_CLIENT_ID: "",
    GOOGLE_CLIENT_SECRET: "",
  };
  let child: ChildProcess | undefined;
  try {
    execFileSync(python, ["-m", "alembic", "upgrade", "head"], {
      cwd: repo,
      env,
      stdio: "pipe",
      timeout: 20000,
    });
    const metadata = JSON.parse(
      execFileSync(python, ["-m", "tests.support_seed"], {
        cwd: repo,
        env,
        encoding: "utf8",
        timeout: 20000,
      }),
    ) as Seed;
    const port = await freePort();
    const base = `http://127.0.0.1:${port}`;
    child = spawn(
      python,
      [
        "-m",
        "uvicorn",
        "backend.app:create_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        String(port),
      ],
      { cwd: repo, env, stdio: ["ignore", "pipe", "pipe"] },
    );
    await waitReady(child);
    const jars: Record<string, string> = {
      ...Object.fromEntries(
        Object.entries(metadata.sessions).map(([role, s]) => [role, s.cookie]),
      ),
    };
    const requests: { method: string; path: string; role: string }[] = [];
    function transport(role: Actor | "anonymous"): typeof fetch {
      return (async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = new URL(String(input));
        if (url.origin !== base)
          throw new Error("Fixture transport only permits own loopback server");
        const headers = new Headers(init?.headers);
        headers.set("Origin", metadata.origin);
        if (jars[role]) headers.set("Cookie", jars[role]);
        requests.push({
          method: init?.method || "GET",
          path: url.pathname,
          role,
        });
        return new Promise<Response>((res, rej) => {
          const req = httpRequest(
            url,
            {
              method: init?.method || "GET",
              headers: Object.fromEntries(headers.entries()),
            },
            (response) => {
              const chunks: Buffer[] = [];
              response.on("data", (chunk) => chunks.push(Buffer.from(chunk)));
              response.on("error", rej);
              response.on("end", () => {
                const outgoing = new Headers();
                Object.entries(response.headers).forEach(([k, v]) => {
                  if (v !== undefined)
                    outgoing.set(k, Array.isArray(v) ? v.join(", ") : v);
                });
                for (const cookie of response.headers["set-cookie"] || []) {
                  if (cookie.startsWith("signaldesk_session=")) {
                    const pair = cookie.split(";")[0];
                    jars[role] =
                      pair === 'signaldesk_session=""' ||
                      pair === "signaldesk_session="
                        ? ""
                        : pair;
                  }
                }
                const bytes = Buffer.concat(chunks);
                res(
                  new Response(
                    response.statusCode === 204 ? null : bytes.toString("utf8"),
                    { status: response.statusCode || 500, headers: outgoing },
                  ),
                );
              });
            },
          );
          req.on("error", rej);
          if (init?.body) req.write(String(init.body));
          req.end();
        });
      }) as typeof fetch;
    }
    const actors = Object.fromEntries(
      (["admin", "marketer", "client"] as const).map((role) => [
        role,
        createApiService(`${base}/api`, transport(role)),
      ]),
    ) as Record<Actor, ReturnType<typeof createApiService>>;
    return {
      metadata,
      base,
      requests,
      api: (role: Actor) => actors[role],
      unauthApi: () => createApiService(`${base}/api`, transport("anonymous")),
      stop: async () => {
        if (child && child.exitCode === null) {
          const finished = once(child, "exit");
          child.kill("SIGTERM");
          await finished;
        }
        rmSync(directory, { recursive: true, force: true });
      },
    };
  } catch (error) {
    child?.kill("SIGTERM");
    rmSync(directory, { recursive: true, force: true });
    throw error;
  }
}
export type HttpFixture = Awaited<ReturnType<typeof startHttpFixture>>;
