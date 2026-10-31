import { describe, expect, it } from "vitest";
import type { SetSummary } from "../types";
import { matchSets } from "./sets";

const s = (code: string, name: string, set_type = "expansion"): SetSummary => ({
  code, name, set_type, released_at: null, card_count: null, icon_svg_uri: null,
});

const sets = [
  s("mh3", "Modern Horizons 3"),
  s("tmh3", "Modern Horizons 3 Tokens", "token"),
  s("mh2", "Modern Horizons 2"),
  s("amh1", "Foo Bar"),
  s("hou", "Hour of Devastation"),
  s("zen", "Zendikar"),
];

describe("matchSets", () => {
  it("matches by code prefix and keeps order", () => {
    expect(matchSets(sets, "mh").map((x) => x.code)).toEqual(["mh3", "mh2"]);
  });
  it("matches by name, case-insensitively", () => {
    expect(matchSets(sets, "HORIZONS").map((x) => x.code)).toEqual(["mh3", "mh2"]);
  });
  it("excludes token, memorabilia and minigame", () => {
    const all = [s("a1", "x a", "token"), s("a2", "x a", "memorabilia"), s("a3", "x a", "minigame")];
    expect(matchSets(all, "a")).toEqual([]);
  });
  it("caps the result", () => {
    const many = Array.from({ length: 9 }, (_, i) => s(`ab${i}`, "n"));
    expect(matchSets(many, "ab")).toHaveLength(5);
    expect(matchSets(many, "ab", 2)).toHaveLength(2);
  });
});
