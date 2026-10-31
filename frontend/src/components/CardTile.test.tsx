import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import type { CardSummary } from "../types";
import CardTile from "./CardTile";

function card(image_url: string | null): CardSummary {
  return { id: "c1", name: "Shock", mana_cost: null, type_line: null, colors: null, rarity: null, set_code: null, image_url };
}
function renderTile(c: CardSummary) {
  return render(<MemoryRouter><CardTile card={c} /></MemoryRouter>);
}

describe("CardTile", () => {
  it("shows a name placeholder and no img when image_url is null", () => {
    renderTile(card(null));
    expect(screen.getByText("Shock")).toBeTruthy();
    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.getByRole("link").getAttribute("href")).toBe("/card/c1");
  });

  it("renders a lazy image with alt text", () => {
    renderTile(card("http://x/y.jpg"));
    const img = screen.getByRole("img");
    expect(img.getAttribute("alt")).toBe("Shock");
    expect(img.getAttribute("loading")).toBe("lazy");
  });

  it("swaps to the placeholder when the image fails to load", () => {
    renderTile(card("http://x/y.jpg"));
    fireEvent.error(screen.getByRole("img"));
    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.getByText("Shock")).toBeTruthy();
  });
});
