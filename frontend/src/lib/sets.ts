import type { SetSummary } from "../types";

const HIDDEN_SET_TYPES = new Set(["token", "memorabilia", "minigame"]);

export function matchSets(sets: SetSummary[], query: string, limit = 5): SetSummary[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return sets
    .filter((s) => !HIDDEN_SET_TYPES.has(s.set_type ?? ""))
    .filter((s) => s.name.toLowerCase().includes(q) || s.code.toLowerCase().startsWith(q))
    .slice(0, limit);
}
