import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it } from "vitest";
import HomePage from "./HomePage";

describe("HomePage", () => {
  it("links to the six color pages", () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    const hrefs = screen
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"))
      .filter((h) => h?.startsWith("/color/"));
    expect(hrefs).toEqual(["/color/w", "/color/u", "/color/b", "/color/r", "/color/g", "/color/c"]);
  });

  it("shows only the big search bar", () => {
    render(<MemoryRouter><HomePage /></MemoryRouter>);
    expect(screen.getAllByPlaceholderText("Search cards or sets…")).toHaveLength(1);
  });
});
