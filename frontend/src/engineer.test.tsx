import { describe, it, expect } from "vitest";
import {
  render,
  screen,
  within,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "./App";
import { aggregate, createMockService, today, validateMetric } from "./service";
describe("Engineer frontend verification", () => {
  it("creates campaign and daily result through forms and loads same day for editing", async () => {
    const m = createMockService(),
      user = userEvent.setup();
    render(<App api={m.service} demo={false} />);
    await screen.findByRole("combobox", { name: "Clients" });
    await user.click(screen.getByRole("button", { name: "New campaign" }));
    let d = screen.getByRole("dialog");
    await user.type(within(d).getByLabelText("Name"), "Engineer journey");
    await user.selectOptions(within(d).getByLabelText("Channel"), "Other");
    await user.click(within(d).getByRole("button", { name: "Save changes" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    const campaign = (await m.service.listCampaigns("c1")).find(
      (p) => p.name === "Engineer journey",
    )!;
    await user.click(screen.getByRole("button", { name: "Add daily results" }));
    d = screen.getByRole("dialog");
    await user.selectOptions(within(d).getByLabelText("Campaign"), campaign.id);
    await within(d).findByText(
      "New daily record. All six values are required.",
    );
    for (const label of [
      "Ad spend",
      "Impressions",
      "Clicks",
      "Leads",
      "Sales",
      "Revenue",
    ])
      await user.type(
        within(d).getByLabelText(label),
        label === "Revenue" ? "400" : "100",
      );
    await user.click(within(d).getByRole("button", { name: "Save changes" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    let rows = (await m.service.listMetrics("c1", today(), today())).filter(
      (r) => r.campaignId === campaign.id,
    );
    expect(rows).toHaveLength(1);
    expect(rows[0].revenue).toBe(400);
    await user.click(screen.getByRole("button", { name: "Add daily results" }));
    d = screen.getByRole("dialog");
    await user.selectOptions(within(d).getByLabelText("Campaign"), campaign.id);
    await within(d).findByText(
      "Existing record loaded. Saving updates this date.",
    );
    const revenue = within(d).getByLabelText("Revenue");
    await waitFor(() => expect(revenue).toHaveValue(400));
    await user.clear(revenue);
    await user.type(revenue, "500");
    await user.click(within(d).getByRole("button", { name: "Save changes" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    rows = (await m.service.listMetrics("c1", today(), today())).filter(
      (r) => r.campaignId === campaign.id,
    );
    expect(rows).toHaveLength(1);
    expect(rows[0].revenue).toBe(500);
    expect(rows[0].version).toBe(2);
  });
  it("shows reversed date range error and switches currencies on client selection", async () => {
    const m = createMockService(),
      user = userEvent.setup();
    render(<App api={m.service} demo={false} />);
    await screen.findByRole("combobox", { name: "Clients" });
    await user.selectOptions(screen.getByLabelText("Clients"), "c2");
    await waitFor(() =>
      expect(screen.getAllByText("USD").length).toBeGreaterThan(0),
    );
    fireEvent.change(screen.getByLabelText("From"), {
      target: { value: "2099-01-01" },
    });
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Start date must not follow end date.",
    );
  });
  it("rejects malformed dates, future dates, negative values and fractional counts", () => {
    const base = {
      campaignId: "x",
      date: today(),
      spend: 1,
      impressions: 10,
      clicks: 1,
      leads: 0,
      sales: 0,
      revenue: 2,
    };
    for (const patch of [
      { date: "2026-02-30" },
      { date: "2099-01-01" },
      { spend: -1 },
      { clicks: 0.1 },
      { revenue: 1.234 },
    ])
      expect(() => validateMetric({ ...base, ...patch })).toThrow();
    expect(() => validateMetric({ ...base, spend: 0 })).not.toThrow();
    expect(aggregate([]).roas).toBeNull();
  });
});
