import { describe, expect, it } from "vitest";
import css from "./styles.css?raw";

// jsdom doesn't apply stylesheets, so the tile size is pinned on the CSS text itself.
describe("styles", () => {
  it("gives every card grid tiles of at least 220px", () => {
    expect(css).toMatch(/\.grid \{[^}]*minmax\(220px, 1fr\)/);
    expect(css).not.toContain("grid-large");
  });
});
