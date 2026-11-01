import type { Color } from "./lib/colors";
import { serializeColors } from "./lib/colors";
import type { AutocompleteCard, CardDetail, CardSummary, Printing, SetSummary, SimilarCard } from "./types";

export class ApiError extends Error {
  status: number;
  detail: string | null;

  constructor(status: number, detail: string | null) {
    super(detail ?? `Request failed (${status})`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, { signal });
  } catch (e) {
    if ((e as { name?: string })?.name === "AbortError") throw e;
    throw new ApiError(0, null);
  }
  if (!res.ok) {
    let detail: string | null = null;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // body is not JSON; keep detail null
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

function withQuery(path: string, params: Record<string, string>): string {
  const qs = new URLSearchParams(params).toString();
  return qs ? `${path}?${qs}` : path;
}

let setsCache: SetSummary[] | null = null;

export function __resetSetsCacheForTests(): void {
  setsCache = null;
}

export const api = {
  autocomplete: (q: string, limit = 10, signal?: AbortSignal) =>
    get<AutocompleteCard[]>(withQuery("/cards/autocomplete", { q, limit: String(limit) }), signal),

  card: (id: string, signal?: AbortSignal) =>
    get<CardDetail>(`/cards/${encodeURIComponent(id)}`, signal),

  printings: (id: string, signal?: AbortSignal) =>
    get<Printing[]>(`/cards/${encodeURIComponent(id)}/printings`, signal),

  similar: (id: string, limit = 12, signal?: AbortSignal) =>
    get<SimilarCard[]>(
      withQuery(`/cards/${encodeURIComponent(id)}/similar`, { limit: String(limit) }),
      signal,
    ),

  sets: async (signal?: AbortSignal): Promise<SetSummary[]> => {
    if (setsCache) return setsCache;
    const result = await get<SetSummary[]>("/sets", signal);
    setsCache = result;
    return result;
  },

  setCards: (code: string, colors: Color[], signal?: AbortSignal) =>
    get<CardSummary[]>(
      withQuery(
        `/sets/${encodeURIComponent(code)}/cards`,
        colors.length ? { colors: serializeColors(colors) } : {},
      ),
      signal,
    ),

  random: (colors: Color[], limit = 100, signal?: AbortSignal) =>
    get<CardSummary[]>(
      withQuery("/cards/random", { colors: serializeColors(colors), limit: String(limit) }),
      signal,
    ),
};
