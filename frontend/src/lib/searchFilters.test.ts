import { describe, expect, it } from "vitest";
import {
  type Filter,
  defaultFilter,
  isComplete,
  parseSearchParams,
  toRequest,
  toSearchParams,
} from "./searchFilters";

describe("searchFilters", () => {
  it("round-trips filters and sort through the URL", () => {
    const filters: Filter[] = [
      { field: "oracle_text", op: "contains", value: "flying" },
      { field: "oracle_text", op: "not_contains", value: "defender" },
      { field: "type", op: "is", value: "Creature" },
      { field: "colors", op: "any", value: ["W", "R", "C"] },
    ];
    const params = toSearchParams(filters, "cmc_asc");
    expect(params.getAll("f")).toContain("colors.any.WRC");
    expect(params.get("sort")).toBe("cmc_asc");
    expect(parseSearchParams(new URLSearchParams(params.toString()))).toEqual({
      filters,
      sort: "cmc_asc",
    });
  });

  it("omits sort for name", () => {
    expect(toSearchParams([defaultFilter()], "name").has("sort")).toBe(false);
  });

  it("keeps dots and ampersands in values", () => {
    const filters: Filter[] = [{ field: "name", op: "contains", value: "a.b & c.d" }];
    const params = new URLSearchParams(toSearchParams(filters, "name").toString());
    expect(parseSearchParams(params).filters).toEqual(filters);
  });

  it("drops invalid parts and falls back to the default filter", () => {
    const params = new URLSearchParams("f=garbage&f=colors.any.XYZ&f=type.is.Goblin&sort=bogus");
    expect(parseSearchParams(params)).toEqual({ filters: [defaultFilter()], sort: "name" });
  });

  it("keeps valid parts next to invalid ones", () => {
    const params = new URLSearchParams("f=bogus.contains.x&f=name.is.x&f=name.contains.elf");
    expect(parseSearchParams(params).filters).toEqual([
      { field: "name", op: "contains", value: "elf" },
    ]);
  });

  it("reads lowercase color letters", () => {
    const { filters } = parseSearchParams(new URLSearchParams("f=colors.any.wrc"));
    expect(filters).toEqual([{ field: "colors", op: "any", value: ["W", "R", "C"] }]);
  });

  it("checks completeness", () => {
    expect(isComplete({ field: "name", op: "contains", value: "  " })).toBe(false);
    expect(isComplete({ field: "name", op: "contains", value: "x".repeat(101) })).toBe(false);
    expect(isComplete({ field: "type", op: "is", value: "" })).toBe(false);
    expect(isComplete({ field: "colors", op: "all", value: [] })).toBe(false);
    expect(isComplete({ field: "colors", op: "all", value: ["G"] })).toBe(true);
  });

  it("returns null request when no row is complete", () => {
    const filters: Filter[] = [defaultFilter(), defaultFilter("colors")];
    expect(toRequest(filters, "name")).toBeNull();
  });

  it("keeps only complete rows, trimmed, in the request", () => {
    const filters: Filter[] = [
      { field: "name", op: "contains", value: "  elf " },
      defaultFilter(),
      { field: "colors", op: "none", value: ["G", "W"] },
    ];
    expect(toRequest(filters, "cmc_desc")).toEqual({
      filters: [
        { field: "name", op: "contains", value: "elf" },
        { field: "colors", op: "none", value: ["W", "G"] },
      ],
      sort: "cmc_desc",
    });
  });
});
