import type { SearchRequest } from "../types";
import type { Color } from "./colors";
import { COLORS, parseColor } from "./colors";

export type Field = "oracle_text" | "name" | "keywords" | "type" | "colors";
export type Op = "contains" | "not_contains" | "is" | "is_not" | "any" | "all" | "none";
export type Filter = { field: Field; op: Op; value: string | Color[] };
export type Sort = "name" | "cmc_asc" | "cmc_desc";

export type ValueKind = "text" | "type" | "colors";

export const MAX_FILTERS = 20;
export const MAX_TEXT_LENGTH = 100;

export const OP_LABELS: Record<Op, string> = {
  contains: "contains",
  not_contains: "does not contain",
  is: "is",
  is_not: "is not",
  any: "has any of",
  all: "has all of",
  none: "has none of",
};

const TEXT_OPS: Op[] = ["contains", "not_contains"];
const COLOR_OPS: Op[] = ["any", "all", "none"];

// kind describes the value input for the default op. A type row switches to a
// text box when its op is contains / not_contains (see valueKind).
export const FIELDS: Record<
  Field,
  { label: string; ops: { op: Op; label: string }[]; defaultOp: Op; kind: ValueKind }
> = {
  oracle_text: { label: "Rules text", ops: withLabels(TEXT_OPS), defaultOp: "contains", kind: "text" },
  name: { label: "Name", ops: withLabels(TEXT_OPS), defaultOp: "contains", kind: "text" },
  keywords: { label: "Keyword", ops: withLabels(TEXT_OPS), defaultOp: "contains", kind: "text" },
  type: {
    label: "Type",
    ops: withLabels(["is", "is_not", ...TEXT_OPS]),
    defaultOp: "is",
    kind: "type",
  },
  colors: { label: "Color", ops: withLabels(COLOR_OPS), defaultOp: "any", kind: "colors" },
};

function withLabels(ops: Op[]): { op: Op; label: string }[] {
  return ops.map((op) => ({ op, label: OP_LABELS[op] }));
}

export const TYPES = [
  "Artifact",
  "Battle",
  "Creature",
  "Enchantment",
  "Instant",
  "Kindred",
  "Land",
  "Planeswalker",
  "Sorcery",
] as const;

const FIELD_NAMES = Object.keys(FIELDS) as Field[];

export function valueKind(field: Field, op: Op): ValueKind {
  if (field === "type") return op === "is" || op === "is_not" ? "type" : "text";
  return FIELDS[field].kind;
}

export function defaultFilter(field: Field = "oracle_text"): Filter {
  const { defaultOp, kind } = FIELDS[field];
  return { field, op: defaultOp, value: kind === "colors" ? [] : "" };
}

function canonicalType(text: string): string | null {
  const lower = text.trim().toLowerCase();
  return TYPES.find((t) => t.toLowerCase() === lower) ?? null;
}

// Returns the cleaned value (trimmed text, canonical type, ordered colors) or null if invalid.
function normaliseValue(field: Field, op: Op, value: string | Color[]): string | Color[] | null {
  if (!FIELDS[field].ops.some((o) => o.op === op)) return null;
  if (field === "colors") {
    if (!Array.isArray(value)) return null;
    const ordered = COLORS.filter((c) => value.includes(c));
    return ordered.length ? ordered : null;
  }
  if (typeof value !== "string") return null;
  if (valueKind(field, op) === "type") return canonicalType(value);
  const text = value.trim();
  return text.length >= 1 && text.length <= MAX_TEXT_LENGTH ? text : null;
}

function cleaned(f: Filter): Filter | null {
  const value = normaliseValue(f.field, f.op, f.value);
  return value === null ? null : { ...f, value };
}

export function isComplete(f: Filter): boolean {
  return cleaned(f) !== null;
}

function completeFilters(filters: Filter[]): Filter[] {
  return filters.flatMap((f) => cleaned(f) ?? []).slice(0, MAX_FILTERS);
}

function parseFilterParam(raw: string): Filter | null {
  // Split on the first two dots only: the value may contain dots.
  const first = raw.indexOf(".");
  const second = first < 0 ? -1 : raw.indexOf(".", first + 1);
  if (second < 0) return null;
  const field = raw.slice(0, first) as Field;
  const op = raw.slice(first + 1, second) as Op;
  const text = raw.slice(second + 1);
  if (!FIELD_NAMES.includes(field)) return null;
  let value: string | Color[] = text;
  if (field === "colors") {
    const colors = [...text].map(parseColor);
    if (colors.some((c) => c === null)) return null;
    value = colors as Color[];
  }
  return cleaned({ field, op, value });
}

export function parseSearchParams(params: URLSearchParams): { filters: Filter[]; sort: Sort } {
  const filters = params
    .getAll("f")
    .flatMap((raw) => parseFilterParam(raw) ?? [])
    .slice(0, MAX_FILTERS);
  const s = params.get("sort");
  const sort: Sort = s === "cmc_asc" || s === "cmc_desc" ? s : "name";
  return { filters: filters.length ? filters : [defaultFilter()], sort };
}

export function toSearchParams(filters: Filter[], sort: Sort): URLSearchParams {
  const params = new URLSearchParams();
  for (const f of completeFilters(filters)) {
    const value = Array.isArray(f.value) ? f.value.join("") : f.value;
    params.append("f", `${f.field}.${f.op}.${value}`);
  }
  if (sort !== "name") params.set("sort", sort);
  return params;
}

export function toRequest(filters: Filter[], sort: Sort): SearchRequest | null {
  const complete = completeFilters(filters);
  if (!complete.length) return null;
  return {
    filters: complete.map((f) => ({ field: f.field, op: f.op, value: f.value })),
    sort,
  };
}
