import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, __resetSetsCacheForTests } from "../api";
import type { CardSummary, SetSummary } from "../types";
import SetPage from "./SetPage";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  api: { setCards: vi.fn(), sets: vi.fn(), autocomplete: vi.fn() },
}));

const CARD: CardSummary = { id: "c1", name: "Shock", mana_cost: null, type_line: null, colors: ["R"], rarity: null, set_code: "mh3", image_url: null };
const MH3: SetSummary = { code: "mh3", name: "Modern Horizons 3", released_at: "2024-06-14", set_type: "draft_innovation", card_count: 100, icon_svg_uri: "https://svgs.example/mh3.svg" };

function Probe() {
  const loc = useLocation();
  return <div data-testid="loc">{loc.pathname + loc.search}</div>;
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Probe />
      <Routes><Route path="/set/:code" element={<SetPage />} /></Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  __resetSetsCacheForTests();
  vi.mocked(api.setCards).mockResolvedValue([CARD]);
  vi.mocked(api.sets).mockResolvedValue([MH3]);
});

describe("SetPage", () => {
  it("renders the set's cards in the large grid", async () => {
    const { container } = renderAt("/set/mh3");
    await screen.findByText("Shock");
    expect(container.querySelector(".grid.grid-large")).not.toBeNull();
  });

  it("loads all cards and shows the header", async () => {
    renderAt("/set/mh3");
    expect(await screen.findByText("Shock")).toBeTruthy();
    expect(api.setCards).toHaveBeenCalledWith("mh3", [], expect.any(AbortSignal));
    expect(await screen.findByText("Modern Horizons 3")).toBeTruthy();
    expect(screen.getByText("MH3 · June 2024")).toBeTruthy();
    expect(document.title).toBe("Modern Horizons 3");
    const icon = document.querySelector("img.seticon");
    expect(icon?.getAttribute("src")).toBe("https://svgs.example/mh3.svg");
    expect(icon?.getAttribute("alt")).toBe("");
  });

  it("falls back to the code when the set is unknown or /sets fails", async () => {
    vi.mocked(api.sets).mockRejectedValue(new ApiError(503, null));
    renderAt("/set/tok");
    expect(await screen.findByText("Shock")).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("TOK");
    expect(document.querySelector("img.seticon")).toBeNull();
  });

  it("toggles chips into the URL and the API call", async () => {
    renderAt("/set/mh3");
    await screen.findByText("Shock");
    const r = screen.getByRole("button", { name: "R" });
    expect(r.getAttribute("aria-pressed")).toBe("false");
    await userEvent.click(r);
    await userEvent.click(screen.getByRole("button", { name: "G" }));
    expect(api.setCards).toHaveBeenLastCalledWith("mh3", ["R", "G"], expect.any(AbortSignal));
    expect(screen.getByTestId("loc").textContent).toBe("/set/mh3?colors=R%2CG");
    expect(screen.getByRole("button", { name: "R" }).getAttribute("aria-pressed")).toBe("true");

    await userEvent.click(screen.getByRole("button", { name: "R" }));
    expect(api.setCards).toHaveBeenLastCalledWith("mh3", ["G"], expect.any(AbortSignal));
    await userEvent.click(screen.getByRole("button", { name: "G" }));
    expect(screen.getByTestId("loc").textContent).toBe("/set/mh3");
  });

  it("ignores invalid colors in the URL", async () => {
    renderAt("/set/mh3?colors=r,X,g");
    expect(await screen.findByText("Shock")).toBeTruthy();
    expect(api.setCards).toHaveBeenCalledWith("mh3", ["R", "G"], expect.any(AbortSignal));
    expect(screen.queryByText("Page not found")).toBeNull();
  });

  it("shows not found on 404", async () => {
    vi.mocked(api.setCards).mockRejectedValue(new ApiError(404, "Set not found."));
    renderAt("/set/zzz");
    expect(await screen.findByText("Set not found")).toBeTruthy();
  });

  it("shows the error copy and retries", async () => {
    vi.mocked(api.setCards).mockRejectedValueOnce(new ApiError(503, null));
    renderAt("/set/mh3");
    expect(await screen.findByText("Couldn't reach the card database. Try again.")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("Shock")).toBeTruthy();
  });
});
