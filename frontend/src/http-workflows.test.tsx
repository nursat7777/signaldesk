import { beforeAll, afterAll, describe, it, expect } from "vitest";
import {
  render,
  screen,
  within,
  waitFor,
  fireEvent,
  cleanup,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { AuthGate } from "./AuthGate";
import { daysAgo, today } from "./service";
import { startHttpFixture, type HttpFixture } from "../test-support/server";
let fixture: HttpFixture;
beforeAll(async () => {
  fixture = await startHttpFixture();
}, 40000);
afterAll(async () => {
  await fixture?.stop();
});
describe("Real HTTP / SQLite / React workflows", () => {
  it("administrator creates client and approved account then assigns existing marketer through actual forms", async () => {
    const user = userEvent.setup();
    const api = fixture.api("admin");
    render(<App api={api} />);
    await screen.findByRole("button", { name: "Agency settings" });
    await user.click(screen.getByRole("button", { name: "Agency settings" }));
    await user.click(await screen.findByRole("button", { name: "Add client" }));
    let d = screen.getByRole("dialog");
    await user.type(within(d).getByLabelText("Name"), "HTTP Created Studio");
    await user.selectOptions(within(d).getByLabelText("Currency"), "EUR");
    await user.click(within(d).getByRole("button", { name: "Save changes" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    const client = (await api.listClients()).find(
      (c) => c.name === "HTTP Created Studio",
    )!;
    expect(client.currency).toBe("EUR");
    await user.click(
      await screen.findByRole("button", { name: "Approve account" }),
    );
    d = screen.getByRole("dialog");
    await user.type(within(d).getByLabelText("Name"), "HTTP Approved Viewer");
    await user.type(
      within(d).getByLabelText("Email"),
      "http.viewer@example.test",
    );
    await user.selectOptions(within(d).getByLabelText("Role"), "client");
    await user.selectOptions(
      within(d).getByLabelText("Client viewer"),
      client.id,
    );
    await user.click(within(d).getByRole("button", { name: "Save changes" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    await screen.findByText("HTTP Approved Viewer");
    const row = screen
      .getByText("Fixture Marketer")
      .closest(".user-row") as HTMLElement;
    await user.click(
      within(row).getByRole("checkbox", { name: "HTTP Created Studio" }),
    );
    await user.click(
      within(row).getByRole("button", { name: "Save assignments" }),
    );
    await waitFor(async () =>
      expect(
        (await api.listUsers()).find((u) => u.name === "Fixture Marketer")
          ?.clientIds,
      ).toContain(client.id),
    );
    expect(
      (await api.listUsers()).find(
        (u) => u.email === "http.viewer@example.test",
      )?.clientId,
    ).toBe(client.id);
  }, 15000);
  it("marketer creates campaign, enters and edits one daily record, viewer sees real report and cannot write/cross clients", async () => {
    const user = userEvent.setup();
    const api = fixture.api("marketer");
    render(<App api={api} />);
    await screen.findByRole("combobox", { name: "Clients" });
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Clients" }),
      fixture.metadata.clientId,
    );
    await user.click(screen.getByRole("button", { name: "New campaign" }));
    let d = screen.getByRole("dialog");
    await user.type(within(d).getByLabelText("Name"), "HTTP Campaign");
    await user.selectOptions(within(d).getByLabelText("Channel"), "Other");
    await user.click(within(d).getByRole("button", { name: "Save changes" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    await user.click(
      await screen.findByRole("button", { name: "Add daily results" }),
    );
    d = screen.getByRole("dialog");
    for (const [label, value] of [
      ["Ad spend", "10.25"],
      ["Impressions", "100"],
      ["Clicks", "20"],
      ["Leads", "4"],
      ["Sales", "2"],
      ["Revenue", "30.75"],
    ])
      await user.type(within(d).getByLabelText(label), value);
    await user.click(within(d).getByRole("button", { name: "Save changes" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    await user.click(screen.getByRole("button", { name: "Add daily results" }));
    d = screen.getByRole("dialog");
    await within(d).findByText(
      "Existing record loaded. Saving updates this date.",
    );
    await waitFor(() =>
      expect(within(d).getByLabelText("Revenue")).toHaveValue(30.75),
    );
    await user.clear(within(d).getByLabelText("Revenue"));
    await user.type(within(d).getByLabelText("Revenue"), "51.25");
    await user.click(within(d).getByRole("button", { name: "Save changes" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    const rows = await api.listMetrics(
      fixture.metadata.clientId,
      today(),
      today(),
    );
    expect(rows).toHaveLength(1);
    expect(rows[0].version).toBe(2);
    expect(rows[0].revenue).toBe(51.25);
    cleanup();
    const viewer = fixture.api("client");
    render(<App api={viewer} />);
    await screen.findByRole("combobox", { name: "Clients" });
    await waitFor(() =>
      expect(screen.getAllByText(/KZT\s51\.25/).length).toBeGreaterThan(0),
    );
    expect(
      screen.queryByRole("button", { name: "Add daily results" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Agency settings" }),
    ).not.toBeInTheDocument();
    await expect(
      viewer.listCampaigns(fixture.metadata.otherClientId),
    ).rejects.toMatchObject({ code: "forbidden" });
    await expect(
      viewer.saveMetric({
        campaignId: rows[0].campaignId,
        date: today(),
        spend: 1,
        impressions: 1,
        clicks: 1,
        leads: 0,
        sales: 0,
        revenue: 1,
        version: 2,
      }),
    ).rejects.toMatchObject({ code: "forbidden" });
    fireEvent.change(screen.getByLabelText("From"), {
      target: { value: daysAgo(100) },
    });
    fireEvent.change(screen.getByLabelText("To"), {
      target: { value: daysAgo(100) },
    });
    await screen.findByText("No results in this period");
    await user.click(screen.getByRole("button", { name: /English/ }));
    await screen.findByText("Аналитика эффективности");
    expect(screen.getByLabelText("Клиенты")).toHaveValue(
      fixture.metadata.clientId,
    );
  }, 15000);
  it("real backend logout revokes fixture session and shows honest unconfigured Google state", async () => {
    render(<AuthGate api={fixture.api("client")} />);
    await screen.findByRole("button", { name: "Sign out" });
    await userEvent.click(screen.getByRole("button", { name: "Sign out" }));
    await screen.findByText("Google sign-in needs configuration");
    await expect(fixture.api("client").getMe()).rejects.toMatchObject({
      code: "unauthorized",
    });
    expect(screen.queryByLabelText("Demo identity")).not.toBeInTheDocument();
    expect(
      fixture.requests.some(
        (r) => r.path === "/api/auth/logout" && r.method === "POST",
      ),
    ).toBe(true);
  });
});
