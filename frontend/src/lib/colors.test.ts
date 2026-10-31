import { describe, expect, it } from "vitest";
import { COLORS, parseColor, parseColorList, serializeColors } from "./colors";

describe("colors", () => {
  it("lists colors in WUBRGC order", () => {
    expect(COLORS).toEqual(["W", "U", "B", "R", "G", "C"]);
  });
  it("parses single colors case-insensitively", () => {
    expect(parseColor("r")).toBe("R");
    expect(parseColor("q")).toBeNull();
    expect(parseColor("RG")).toBeNull();
  });
  it("drops invalid letters and duplicates, sorts", () => {
    expect(parseColorList("r,X,r,g")).toEqual(["R", "G"]);
    expect(parseColorList("g,w")).toEqual(["W", "G"]);
    expect(parseColorList(null)).toEqual([]);
  });
  it("serializes in WUBRGC order", () => {
    expect(serializeColors(["G", "R", "W"])).toBe("W,R,G");
    expect(serializeColors([])).toBe("");
  });
});
