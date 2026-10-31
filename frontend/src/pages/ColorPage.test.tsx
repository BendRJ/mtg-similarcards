import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "../api";
import type { CardSummary } from "../types";
import ColorPage from "./ColorPage";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  api: { random: vi.fn(), autocomplete: vi.fn(), sets: vi.fn() },
}));

const CARD: CardSummary = { id: "c1", name: "Shock", mana_cost: null, type_line: null, colors: ["R"], rarity: null, set_code: null, image_url: null };

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes><Route path="/color/:c" element={<ColorPage />} /></Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.random).mockResolvedValue([CARD]);
});

describe("ColorPage", () => {
  it("loads random cards for the color", async () => {
    renderAt("/color/r");
    expect(await screen.findByText("Shock")).toBeTruthy();
    expect(screen.getByText("Random red cards")).toBeTruthy();
    expect(document.title).toBe("Random red cards");
    expect(api.random).toHaveBeenCalledWith(["R"], 100, expect.any(AbortSignal));
  });

  it("shows the color pip in the header", async () => {
    renderAt("/color/r");
    await screen.findByText("Shock");
    const pip = screen.getAllByRole("link", { name: "Random red cards" })[0];
    expect(pip.textContent).toBe("R");
  });

  it("shows not found for an unknown color without calling the API", () => {
    renderAt("/color/x");
    expect(screen.getByText("Page not found")).toBeTruthy();
    expect(api.random).not.toHaveBeenCalled();
  });

  it("shuffle loads again", async () => {
    renderAt("/color/r");
    await screen.findByText("Shock");
    await userEvent.click(screen.getByRole("button", { name: "Shuffle" }));
    await screen.findByText("Shock");
    expect(api.random).toHaveBeenCalledTimes(2);
  });

  it("shows the error copy and retries", async () => {
    vi.mocked(api.random).mockRejectedValueOnce(new ApiError(503, null));
    renderAt("/color/r");
    expect(await screen.findByText("Couldn't reach the card database. Try again.")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("Shock")).toBeTruthy();
    expect(api.random).toHaveBeenCalledTimes(2);
  });
});
