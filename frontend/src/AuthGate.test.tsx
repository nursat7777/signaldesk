import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AuthGate } from "./AuthGate";
import { createMockService, ServiceError } from "./service";
import type { AuthService } from "./api-service";
function api(configured = false): AuthService {
  return {
    ...createMockService().service,
    getMe: vi.fn().mockRejectedValue(new ServiceError("unauthorized")),
    authStatus: vi.fn().mockResolvedValue({ configured }),
    logout: vi.fn().mockResolvedValue(undefined),
    loginUrl: "/api/auth/google",
  };
}
describe("Production authentication shell", () => {
  it("shows honest unconfigured state with no mock identities and localizes it", async () => {
    render(<AuthGate api={api()} />);
    await screen.findByText("Google sign-in needs configuration");
    expect(
      screen.queryByRole("link", { name: /Continue with Google/ }),
    ).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Demo identity")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Русский/ }));
    expect(
      screen.getByText("Необходимо настроить вход через Google"),
    ).toBeInTheDocument();
  });
  it("offers real Google URL only when configured", async () => {
    render(<AuthGate api={api(true)} />);
    expect(
      await screen.findByRole("link", { name: /Continue with Google/ }),
    ).toHaveAttribute("href", "/api/auth/google");
  });
  it("renders authorized workspace and signs out using backend", async () => {
    const m = createMockService();
    let loggedOut = false;
    const auth: AuthService = {
      ...m.service,
      getMe: async () => {
        if (loggedOut) throw new ServiceError("unauthorized");
        return m.service.getMe();
      },
      authStatus: async () => ({ configured: true }),
      logout: async () => {
        loggedOut = true;
      },
      loginUrl: "/api/auth/google",
    };
    render(<AuthGate api={auth} />);
    await screen.findByRole("button", { name: "Sign out" });
    expect(screen.queryByLabelText("Demo identity")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
    await screen.findByRole("link", { name: /Continue with Google/ });
    expect(loggedOut).toBe(true);
  });
  it("shows retry after network failure, never renders workspace", async () => {
    const a = api();
    a.getMe = vi.fn().mockRejectedValue(new ServiceError("network"));
    render(<AuthGate api={a} />);
    await screen.findByRole("alert");
    expect(
      screen.queryByRole("button", { name: "Add daily results" }),
    ).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(a.getMe).toHaveBeenCalledTimes(2));
  });
});
