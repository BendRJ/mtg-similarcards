import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api";
import type { CardSummary, SetSummary } from "../types";
import SearchBar from "./SearchBar";

vi.mock("../api");

function card(id: string, name: string): CardSummary {
  return { id, name, mana_cost: null, type_line: "Instant", colors: null, rarity: null, set_code: "mh3", image_url: null };
}
const SETS: SetSummary[] = [
  { code: "mh3", name: "Modern Horizons 3", released_at: "2024-06-14", set_type: "draft_innovation", card_count: 1, icon_svg_uri: null },
];

function deferred<T>() {
  let resolve!: (v: T) => void;
  const promise = new Promise<T>((res) => { resolve = res; });
  return { promise, resolve };
}

function Where() {
  const loc = useLocation();
  return <div data-testid="where">{loc.pathname}</div>;
}

function setup() {
  const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
  render(
    <MemoryRouter>
      <SearchBar />
      <Routes>
        <Route path="*" element={<Where />} />
      </Routes>
    </MemoryRouter>,
  );
  return { user, input: screen.getByRole("combobox") };
}

async function settle() {
  await act(async () => { await vi.advanceTimersByTimeAsync(150); });
}

describe("SearchBar", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Testing Library only advances fake timers in its async helpers when a `jest` global exists.
    vi.stubGlobal("jest", { advanceTimersByTime: vi.advanceTimersByTime.bind(vi) });
    vi.mocked(api.sets).mockResolvedValue(SETS);
    vi.mocked(api.autocomplete).mockResolvedValue([card("c1", "Modern Age"), card("c2", "Modular Monstrosity")]);
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it("waits for two characters before searching", async () => {
    const { user, input } = setup();
    expect(input.getAttribute("placeholder")).toBe("Search cards or sets…");
    await user.type(input, "b");
    await settle();
    expect(api.autocomplete).not.toHaveBeenCalled();
    await user.type(input, "o");
    await settle();
    expect(api.autocomplete).toHaveBeenCalledTimes(1);
    expect(vi.mocked(api.autocomplete).mock.calls[0][0]).toBe("bo");
  });

  it("lists cards first, then sets, with group headers", async () => {
    const { user, input } = setup();
    await user.type(input, "mod");
    await settle();
    const options = screen.getAllByRole("option");
    expect(options.map((o) => o.textContent)).toEqual([
      expect.stringContaining("Modern Age"),
      expect.stringContaining("Modular Monstrosity"),
      expect.stringContaining("Modern Horizons 3"),
    ]);
    expect(screen.getByText("Cards")).toBeTruthy();
    expect(screen.getByText("Sets")).toBeTruthy();
    expect(options[0].textContent).toContain("Instant · MH3");
    expect(options[2].textContent).toContain("MH3 · 2024");
  });

  it("navigates to the highlighted row with Enter", async () => {
    const { user, input } = setup();
    await user.type(input, "mod");
    await settle();
    await user.keyboard("{ArrowDown}{ArrowDown}{ArrowDown}{Enter}");
    expect(screen.getByTestId("where").textContent).toBe("/set/mh3");
  });

  it("opens the first row when Enter is pressed with nothing highlighted", async () => {
    const { user, input } = setup();
    await user.type(input, "mod");
    await settle();
    await user.keyboard("{Enter}");
    expect(screen.getByTestId("where").textContent).toBe("/card/c1");
  });

  it("ArrowDown then Enter opens the first card; ArrowUp wraps to the last row", async () => {
    const { user, input } = setup();
    await user.type(input, "mod");
    await settle();
    await user.keyboard("{ArrowDown}");
    expect(input.getAttribute("aria-activedescendant")).toBe(screen.getAllByRole("option")[0].id);
    await user.keyboard("{ArrowUp}");
    expect(input.getAttribute("aria-activedescendant")).toBe(screen.getAllByRole("option")[2].id);
    await user.keyboard("{ArrowDown}{Enter}");
    expect(screen.getByTestId("where").textContent).toBe("/card/c1");
  });

  it("closes the dropdown with Escape", async () => {
    const { user, input } = setup();
    await user.type(input, "mod");
    await settle();
    expect(screen.queryByRole("listbox")).not.toBeNull();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("closes the dropdown when clicking outside", async () => {
    const { user, input } = setup();
    await user.type(input, "mod");
    await settle();
    await user.click(document.body);
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("ignores a stale response that arrives after a newer one", async () => {
    const slow = deferred<CardSummary[]>();
    const fast = deferred<CardSummary[]>();
    vi.mocked(api.autocomplete).mockImplementation((q) => (q === "bo" ? slow.promise : fast.promise));
    const { user, input } = setup();
    await user.type(input, "bo");
    await settle();
    await user.type(input, "l");
    await settle();
    await act(async () => { fast.resolve([card("c9", "Bolt")]); });
    await act(async () => { slow.resolve([card("c8", "Boros Charm")]); });
    const names = screen.getAllByRole("option").map((o) => o.textContent ?? "");
    expect(names.some((n) => n.includes("Bolt"))).toBe(true);
    expect(names.some((n) => n.includes("Boros Charm"))).toBe(false);
  });

  it("shows a message when nothing matches", async () => {
    vi.mocked(api.autocomplete).mockResolvedValue([]);
    const { user, input } = setup();
    await user.type(input, "zzz");
    await settle();
    expect(screen.getByText("No cards or sets found")).toBeTruthy();
  });

  it("still shows sets when autocomplete fails", async () => {
    vi.mocked(api.autocomplete).mockRejectedValue(new Error("boom"));
    const { user, input } = setup();
    await user.type(input, "mod");
    await settle();
    expect(screen.getAllByRole("option")).toHaveLength(1);
  });
});
