import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "../api";
import type { CardDetail, Printing, SimilarCard } from "../types";
import CardPage from "./CardPage";

vi.mock("../api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api")>()),
  api: { card: vi.fn(), printings: vi.fn(), similar: vi.fn(), autocomplete: vi.fn(), sets: vi.fn() },
}));

function detail(id: string, name: string, oracle: string): CardDetail {
  return {
    id, name, mana_cost: "{1}{R}", type_line: "Instant", colors: ["R"], rarity: "common", set_code: "lea",
    image_url: null, image_url_large: null, oracle_id: null, cmc: 2, oracle_text: oracle, flavor_text: null, power: null,
    toughness: null, loyalty: null, keywords: null, color_identity: null, set_name: "Alpha",
    collector_number: "12", released_at: null, artist: "Jane Doe", legalities: null,
  };
}
function printing(id: string, set: string): Printing {
  return { id, set_code: set, set_name: set, collector_number: "1", released_at: "2020-01-01", rarity: "common", image_url: null };
}
const SIMILAR: SimilarCard = { id: "s1", name: "Lightning Bolt", mana_cost: null, type_line: null, colors: null, rarity: null, set_code: null, image_url: null, distance: 0.1 };

function page(cards: SimilarCard[], has_more = false) {
  return { cards, has_more };
}
function similarCard(id: string, name: string): SimilarCard {
  return { ...SIMILAR, id, name };
}

function Where() {
  const loc = useLocation();
  return <div data-testid="where">{loc.pathname + loc.search}</div>;
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes><Route path="/card/:id" element={<><CardPage /><Where /></>} /></Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.card).mockResolvedValue(detail("a1", "Shock", "Deals 2 damage."));
  vi.mocked(api.printings).mockResolvedValue([printing("a1", "lea"), printing("a2", "2x2")]);
  vi.mocked(api.similar).mockResolvedValue(page([SIMILAR]));
});

describe("CardPage", () => {
  it("renders details, highlights the current printing and sets the title", async () => {
    renderAt("/card/a1");
    expect(await screen.findByRole("heading", { name: /Shock/ })).toBeTruthy();
    expect(screen.getByText("Instant")).toBeTruthy();
    expect(screen.getByText("Deals 2 damage.")).toBeTruthy();
    expect(screen.getByText("Jane Doe", { exact: false })).toBeTruthy();
    const current = await screen.findByRole("link", { name: /lea/i });
    expect(current.getAttribute("aria-current")).toBe("true");
    expect(current.getAttribute("href")).toBe("/card/a1");
    expect(screen.getByRole("link", { name: /2x2/i }).getAttribute("aria-current")).toBeNull();
    expect(await screen.findByText("Lightning Bolt")).toBeTruthy();
    expect(document.title).toBe("Shock");
    expect(screen.getByText("Mana value").nextElementSibling?.textContent).toBe("2");
    expect(screen.getByText("Rarity").nextElementSibling?.textContent).toBe("common");
    expect(api.similar).toHaveBeenCalledWith("a1", { filters: [], limit: 12, offset: 0 }, expect.any(AbortSignal));
  });

  it("shows the large image on the card page", async () => {
    vi.mocked(api.card).mockResolvedValue({
      ...detail("a1", "Shock", "x"), image_url: "https://x/n.jpg", image_url_large: "https://x/l.jpg",
    });
    renderAt("/card/a1");
    const img = await screen.findByRole("img", { name: "Shock" });
    expect(img.getAttribute("src")).toBe("https://x/l.jpg");
  });

  it("falls back to the normal image when there is no large one", async () => {
    vi.mocked(api.card).mockResolvedValue({
      ...detail("a1", "Shock", "x"), image_url: "https://x/n.jpg", image_url_large: null,
    });
    renderAt("/card/a1");
    const img = await screen.findByRole("img", { name: "Shock" });
    expect(img.getAttribute("src")).toBe("https://x/n.jpg");
  });

  it("renders similar cards in a card grid", async () => {
    const { container } = renderAt("/card/a1");
    await screen.findByText("Lightning Bolt");
    expect(container.querySelector(".grid")).not.toBeNull();
  });

  it("applies the filters from the URL and keeps them on similar-card links", async () => {
    renderAt("/card/a1?f=type.contains.Creature&f=colors.any.G");
    const tile = await screen.findByRole("link", { name: "Lightning Bolt" });
    expect(api.similar).toHaveBeenCalledWith("a1", {
      filters: [{ field: "type", op: "contains", value: "Creature" }, { field: "colors", op: "any", value: ["G"] }],
      limit: 12, offset: 0,
    }, expect.any(AbortSignal));
    expect(tile.getAttribute("href")).toBe("/card/s1?f=type.contains.Creature&f=colors.any.G");
    expect(screen.getByRole("button", { name: "Filter similar cards" }).getAttribute("aria-expanded")).toBe("true");
  });

  it("builds a filter in the panel and applies it through the URL", async () => {
    const user = userEvent.setup();
    renderAt("/card/a1");
    await screen.findByText("Lightning Bolt");
    const toggle = screen.getByRole("button", { name: "Filter similar cards" });
    expect(toggle.getAttribute("aria-expanded")).toBe("false");
    await user.click(toggle);
    await user.selectOptions(screen.getByRole("combobox", { name: "Field" }), "type");
    await user.selectOptions(screen.getByRole("combobox", { name: "Condition" }), "contains");
    await user.type(screen.getByRole("textbox", { name: "Value" }), "Creature");
    await user.click(screen.getByRole("button", { name: "Apply filters" }));
    expect(screen.getByTestId("where").textContent).toBe("/card/a1?f=type.contains.Creature");
    expect(api.similar).toHaveBeenLastCalledWith("a1", {
      filters: [{ field: "type", op: "contains", value: "Creature" }], limit: 12, offset: 0,
    }, expect.any(AbortSignal));
  });

  it("clears the filters", async () => {
    const user = userEvent.setup();
    renderAt("/card/a1?f=type.contains.Creature");
    await screen.findByText("Lightning Bolt");
    await user.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(screen.getByTestId("where").textContent).toBe("/card/a1");
  });

  it("shows no matches when the filters leave nothing", async () => {
    vi.mocked(api.similar).mockResolvedValue(page([]));
    renderAt("/card/a1?f=type.contains.Creature");
    expect(await screen.findByText("No similar cards match these filters.")).toBeTruthy();
  });

  it("loads more similar cards with Show more until there are none left", async () => {
    const user = userEvent.setup();
    vi.mocked(api.similar)
      .mockResolvedValueOnce(page([similarCard("s1", "First")], true))
      .mockResolvedValueOnce(page([similarCard("s2", "Second")], false));
    renderAt("/card/a1");
    await screen.findByText("First");
    await user.click(screen.getByRole("button", { name: "Show more" }));
    expect(await screen.findByText("Second")).toBeTruthy();
    expect(screen.getByText("First")).toBeTruthy();
    expect(api.similar).toHaveBeenLastCalledWith("a1", { filters: [], limit: 12, offset: 1 }, expect.any(AbortSignal));
    expect(screen.queryByRole("button", { name: "Show more" })).toBeNull();
  });

  it("shows a hint when similar cards are unavailable but keeps the page", async () => {
    vi.mocked(api.similar).mockRejectedValue(new ApiError(404, "No embedding for this card yet."));
    renderAt("/card/a1");
    expect(await screen.findByText("Similar cards aren't available for this card yet")).toBeTruthy();
    expect(screen.getByText("Deals 2 damage.")).toBeTruthy();
  });

  it("shows the error state when similar fails otherwise", async () => {
    vi.mocked(api.similar).mockRejectedValue(new ApiError(500, null));
    renderAt("/card/a1");
    expect(await screen.findByText("Couldn't reach the card database. Try again.")).toBeTruthy();
  });

  it("shows not found when the card does not exist", async () => {
    vi.mocked(api.card).mockRejectedValue(new ApiError(404, "Card not found."));
    vi.mocked(api.printings).mockRejectedValue(new ApiError(404, "Card not found."));
    vi.mocked(api.similar).mockRejectedValue(new ApiError(404, "Card not found."));
    renderAt("/card/zz");
    expect(await screen.findByText("Card not found")).toBeTruthy();
  });

  it("refetches on route change and never mixes old and new data", async () => {
    let resolveCard!: (c: CardDetail) => void;
    renderAt("/card/a1");
    await screen.findByRole("heading", { name: /Shock/ });
    await screen.findByRole("link", { name: /2x2/i });

    vi.mocked(api.card).mockReturnValue(new Promise((r) => { resolveCard = r; }));
    vi.mocked(api.printings).mockResolvedValue([printing("s1", "mh3")]);
    await userEvent.click(await screen.findByRole("link", { name: /Lightning Bolt/ }));

    expect(api.card).toHaveBeenCalledWith("s1", expect.any(AbortSignal));
    expect(screen.queryByText(/Shock/)).toBeNull();
    expect(screen.queryByText("Deals 2 damage.")).toBeNull();
    expect(screen.queryByRole("link", { name: /2x2/i })).toBeNull();

    resolveCard(detail("s1", "Lightning Bolt", "Deals 3 damage."));
    expect(await screen.findByText("Deals 3 damage.")).toBeTruthy();
    expect(screen.queryByRole("link", { name: /2x2/i })).toBeNull();
    expect((await screen.findByRole("link", { name: /mh3/i })).getAttribute("aria-current")).toBe("true");
  });
});
