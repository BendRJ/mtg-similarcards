import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "../api";
import { toSearchParams } from "../lib/searchFilters";
import type { Filter } from "../lib/searchFilters";
import type { CardSummary } from "../types";
import AdvancedSearchPage from "./AdvancedSearchPage";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  api: { search: vi.fn(), autocomplete: vi.fn() },
}));

function card(i: number): CardSummary {
  return { id: `c${i}`, name: `Card ${i}`, mana_cost: null, type_line: null, colors: [], rarity: null, set_code: null, image_url: null };
}

function Probe() {
  const loc = useLocation();
  return <div data-testid="loc">{loc.search}</div>;
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Probe />
      <Routes><Route path="/search" element={<AdvancedSearchPage />} /></Routes>
    </MemoryRouter>,
  );
}

const rows = () => screen.getAllByLabelText("Field");
const nth = (label: string, i: number) => screen.getAllByLabelText(label)[i]!;

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.search).mockResolvedValue({ total: 1, cards: [card(1)] });
});

describe("AdvancedSearchPage", () => {
  it("builds the example through the UI and searches", async () => {
    const user = userEvent.setup();
    renderAt("/search");
    await user.selectOptions(nth("Field", 0), "oracle_text");
    await user.type(nth("Value", 0), "artifact");
    for (let i = 0; i < 4; i++) await user.click(screen.getByRole("button", { name: "+ Add filter" }));
    expect(rows()).toHaveLength(5);
    await user.type(nth("Value", 1), "token");
    await user.selectOptions(nth("Condition", 2), "not_contains");
    await user.type(nth("Value", 2), "clue");
    await user.selectOptions(nth("Field", 3), "type");
    await user.selectOptions(nth("Value", 3), "Land");
    await user.selectOptions(nth("Field", 4), "colors");
    const row5 = within(nth("Field", 4).closest(".filter-row") as HTMLElement);
    for (const c of ["W", "R", "C"]) await user.click(row5.getByRole("button", { name: c }));
    await user.click(screen.getByRole("button", { name: "+ Add filter" }));
    await user.selectOptions(nth("Field", 5), "colors");
    await user.selectOptions(nth("Condition", 5), "none");
    const row6 = within(nth("Field", 5).closest(".filter-row") as HTMLElement);
    for (const c of ["U", "B", "G"]) await user.click(row6.getByRole("button", { name: c }));
    await user.selectOptions(screen.getByLabelText("Sort by"), "cmc_asc");
    expect(api.search).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Search" }));

    const state: Filter[] = [
      { field: "oracle_text", op: "contains", value: "artifact" },
      { field: "oracle_text", op: "contains", value: "token" },
      { field: "oracle_text", op: "not_contains", value: "clue" },
      { field: "type", op: "is", value: "Land" },
      { field: "colors", op: "any", value: ["W", "R", "C"] },
      { field: "colors", op: "none", value: ["U", "B", "G"] },
    ];
    expect(await screen.findByText("Card 1")).toBeTruthy();
    expect(api.search).toHaveBeenCalledTimes(1);
    expect(api.search).toHaveBeenCalledWith({ filters: state, sort: "cmc_asc" }, expect.any(AbortSignal));
    expect(screen.getByTestId("loc").textContent).toBe("?" + toSearchParams(state, "cmc_asc").toString());
  });

  it("searches on Enter in a text input", async () => {
    const user = userEvent.setup();
    renderAt("/search");
    await user.type(nth("Value", 0), "flying{Enter}");
    expect(await screen.findByText("Card 1")).toBeTruthy();
    expect(screen.getByTestId("loc").textContent).toBe("?f=oracle_text.contains.flying");
  });

  it("runs the search from the URL on load", async () => {
    renderAt("/search?f=oracle_text.contains.artifact");
    expect(await screen.findByText("Card 1")).toBeTruthy();
    expect(screen.getByText("1 cards")).toBeTruthy();
    expect(api.search).toHaveBeenCalledWith(
      { filters: [{ field: "oracle_text", op: "contains", value: "artifact" }], sort: "name" },
      expect.any(AbortSignal),
    );
    expect((nth("Value", 0) as HTMLInputElement).value).toBe("artifact");
    expect(document.title).toBe("Advanced search");
  });

  it("makes no request without filters and shows a hint", () => {
    renderAt("/search");
    expect(api.search).not.toHaveBeenCalled();
    expect(screen.getByText("Add at least one filter with a value, then press Search.")).toBeTruthy();
  });

  it("removes a row from the next request", async () => {
    const user = userEvent.setup();
    renderAt("/search?f=oracle_text.contains.a&f=name.contains.b");
    await screen.findByText("Card 1");
    await user.click(screen.getAllByRole("button", { name: "Remove filter" })[0]!);
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(api.search).toHaveBeenLastCalledWith(
      { filters: [{ field: "name", op: "contains", value: "b" }], sort: "name" },
      expect.any(AbortSignal),
    );
    expect(screen.getByTestId("loc").textContent).toBe("?f=name.contains.b");
  });

  it("shows chips and resets the value when the field changes to Color", async () => {
    const user = userEvent.setup();
    renderAt("/search");
    await user.type(nth("Value", 0), "abc");
    await user.selectOptions(nth("Field", 0), "colors");
    expect(screen.queryByLabelText("Value")).toBeNull();
    const chips = ["W", "U", "B", "R", "G", "C"].map((c) => screen.getByRole("button", { name: c }));
    expect(chips.every((c) => c.getAttribute("aria-pressed") === "false")).toBe(true);
    await user.click(chips[0]!);
    expect(chips[0]!.getAttribute("aria-pressed")).toBe("true");
    await user.selectOptions(nth("Field", 0), "name");
    expect((nth("Value", 0) as HTMLInputElement).value).toBe("");
  });

  it("resets a Type value when switching between list and text conditions", async () => {
    const user = userEvent.setup();
    renderAt("/search");
    await user.selectOptions(nth("Field", 0), "type");
    await user.selectOptions(nth("Value", 0), "Land");
    await user.selectOptions(nth("Condition", 0), "contains");
    const input = nth("Value", 0) as HTMLInputElement;
    expect(input.tagName).toBe("INPUT");
    expect(input.value).toBe("");
    await user.type(input, "goblin");
    await user.selectOptions(nth("Condition", 0), "is_not");
    expect((nth("Value", 0) as HTMLSelectElement).tagName).toBe("SELECT");
    expect((nth("Value", 0) as HTMLSelectElement).value).toBe("");
  });

  it("disables Add filter at 20 rows", async () => {
    const user = userEvent.setup();
    renderAt("/search");
    const add = screen.getByRole("button", { name: "+ Add filter" }) as HTMLButtonElement;
    for (let i = 0; i < 19; i++) await user.click(add);
    expect(rows()).toHaveLength(20);
    expect(add.disabled).toBe(true);
    await user.click(screen.getAllByRole("button", { name: "Remove filter" })[0]!);
    expect(add.disabled).toBe(false);
  });

  it("shows the total and the first-200 note", async () => {
    vi.mocked(api.search).mockResolvedValue({ total: 250, cards: Array.from({ length: 200 }, (_, i) => card(i)) });
    renderAt("/search?f=name.contains.a");
    expect(await screen.findByText("250 cards · showing the first 200")).toBeTruthy();
  });

  it("shows the empty state", async () => {
    vi.mocked(api.search).mockResolvedValue({ total: 0, cards: [] });
    renderAt("/search?f=name.contains.a");
    expect(await screen.findByText("No cards match these filters.")).toBeTruthy();
  });

  it("shows the error copy", async () => {
    vi.mocked(api.search).mockRejectedValue(new ApiError(503, null));
    renderAt("/search?f=name.contains.a");
    expect(await screen.findByText("Couldn't reach the card database. Try again.")).toBeTruthy();
  });

  it("links to the advanced search from the top bar", () => {
    renderAt("/search");
    const link = screen.getByRole("link", { name: "Advanced search" });
    expect(link.getAttribute("href")).toBe("/search");
  });
});
