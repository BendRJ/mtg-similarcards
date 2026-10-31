import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import App from "./App";

const FOOTER = "Card data and images via Scryfall. Magic: The Gathering is © Wizards of the Coast.";

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("App routing", () => {
  it("shows the footer on the home page", () => {
    renderAt("/");
    expect(screen.getByText(FOOTER)).toBeTruthy();
  });

  it("shows not found for an unknown path", () => {
    renderAt("/nope");
    expect(screen.getByText("Page not found")).toBeTruthy();
  });

  it("shows not found for the plural API path /cards", () => {
    renderAt("/cards");
    expect(screen.getByText("Page not found")).toBeTruthy();
  });
});
