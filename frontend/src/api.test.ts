import { beforeEach, describe, expect, it, vi } from "vitest";
import type { SimilarRequest } from "./types";
import { ApiError, __resetSetsCacheForTests, api } from "./api";

function stubFetch(body: unknown, status = 200) {
  const fn = vi.fn().mockImplementation(async () =>
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }),
  );
  vi.stubGlobal("fetch", fn);
  return fn;
}

const url = (fn: ReturnType<typeof vi.fn>) => fn.mock.calls[0][0];

describe("api", () => {
  beforeEach(() => __resetSetsCacheForTests());

  it("encodes autocomplete query", async () => {
    const fn = stubFetch([]);
    await api.autocomplete("a&b #%/ c");
    expect(url(fn)).toBe("/cards/autocomplete?q=a%26b+%23%25%2F+c&limit=10");
  });

  it("omits colors for empty set filter", async () => {
    const fn = stubFetch([]);
    await api.setCards("mh3", []);
    expect(url(fn)).toBe("/sets/mh3/cards");
  });

  it("sends set colors in WUBRGC order", async () => {
    const fn = stubFetch([]);
    await api.setCards("mh3", ["G", "R"]);
    expect(url(fn)).toBe("/sets/mh3/cards?colors=R%2CG");
  });

  it("requests random cards", async () => {
    const fn = stubFetch([]);
    await api.random(["R"]);
    expect(url(fn)).toBe("/cards/random?colors=R&limit=100");
  });

  it("builds card, printings and similar urls", async () => {
    const fn = stubFetch({});
    await api.card("a/b");
    await api.printings("x");
    expect(fn.mock.calls.map((c) => c[0])).toEqual(["/cards/a%2Fb", "/cards/x/printings"]);
  });

  it("posts the similar request with filters, limit and offset", async () => {
    const fn = stubFetch({ cards: [], has_more: false });
    const req: SimilarRequest = { filters: [{ field: "type", op: "contains", value: "Creature" }], limit: 12, offset: 24 };
    await api.similar("a/b", req);
    expect(fn.mock.calls[0][0]).toBe("/cards/a%2Fb/similar");
    expect(fn.mock.calls[0][1].method).toBe("POST");
    expect(JSON.parse(fn.mock.calls[0][1].body)).toEqual(req);
  });

  it("passes the signal to fetch", async () => {
    const fn = stubFetch({});
    const ctrl = new AbortController();
    await api.card("x", ctrl.signal);
    expect(fn.mock.calls[0][1]).toEqual({ signal: ctrl.signal });
  });

  it("maps 404 to ApiError with detail", async () => {
    stubFetch({ detail: "Card not found." }, 404);
    const err = await api.card("x").catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(404);
    expect(err.detail).toBe("Card not found.");
  });

  it("uses null detail when body detail is not a string", async () => {
    stubFetch({ detail: [{ msg: "bad" }] }, 422);
    const err = await api.card("x").catch((e) => e);
    expect(err.status).toBe(422);
    expect(err.detail).toBeNull();
  });

  it("maps network failure to status 0", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    const err = await api.card("x").catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(0);
    expect(err.detail).toBeNull();
  });

  it("lets AbortError through", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new DOMException("aborted", "AbortError")));
    const err = await api.card("x").catch((e) => e);
    expect(err).not.toBeInstanceOf(ApiError);
    expect(err.name).toBe("AbortError");
  });

  it("caches sets after first success", async () => {
    const fn = stubFetch([{ code: "mh3", name: "MH3" }]);
    await api.sets();
    const again = await api.sets();
    expect(fn).toHaveBeenCalledTimes(1);
    expect(again).toHaveLength(1);
  });

  it("does not cache a failed sets call", async () => {
    stubFetch({ detail: "boom" }, 500);
    await api.sets().catch(() => undefined);
    const fn = stubFetch([]);
    await api.sets();
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("posts the search request as JSON", async () => {
    const fn = stubFetch({ total: 0, cards: [] });
    const req = { filters: [{ field: "name" as const, op: "contains", value: "elf" }], sort: "name" as const };
    await api.search(req);
    expect(url(fn)).toBe("/cards/search");
    const init = fn.mock.calls[0][1];
    expect(init.method).toBe("POST");
    expect(init.headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(init.body)).toEqual(req);
  });

  it("maps a 422 on search to ApiError", async () => {
    stubFetch({ detail: "bad" }, 422);
    await expect(api.search({ filters: [], sort: "name" })).rejects.toMatchObject({
      name: "ApiError",
      status: 422,
    });
  });
});
