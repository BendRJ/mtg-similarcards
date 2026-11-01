import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useSearchParams } from "react-router";
import { api, ApiError } from "../api";
import { MAX_FILTERS, defaultFilter, filtersQuery, parseSearchParams, toRequest, toSearchParams } from "../lib/searchFilters";
import type { Filter } from "../lib/searchFilters";
import { useAsync } from "../lib/useAsync";
import type { SimilarCard } from "../types";
import CardGrid from "./CardGrid";
import ErrorState from "./ErrorState";
import FilterRow from "./FilterRow";
import Loading from "./Loading";

const PAGE_SIZE = 12;

export default function SimilarCards({ id }: { id: string }) {
  const [searchParams] = useSearchParams();
  // key remounts the section when the filters in the URL change, so the form, the first page
  // and any "Show more" pages always belong to the same filters.
  return <SimilarView key={searchParams.toString()} id={id} />;
}

function SimilarView({ id }: { id: string }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const applied = parseSearchParams(searchParams);
  const filters = toRequest(applied.filters, "name")?.filters ?? [];
  const search = filtersQuery(searchParams);

  const [open, setOpen] = useState(filters.length > 0);
  const [rows, setRows] = useState<Filter[]>(applied.filters);

  const first = useAsync(
    (s) => api.similar(id, { filters, limit: PAGE_SIZE, offset: 0 }, s),
    [id, searchParams.toString()],
  );
  const [more, setMore] = useState<SimilarCard[]>([]);
  const [hasMore, setHasMore] = useState<boolean | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [moreError, setMoreError] = useState<ApiError | null>(null);
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);

  function apply(e: FormEvent) {
    e.preventDefault();
    setSearchParams(toSearchParams(rows, "name"));
  }

  async function showMore() {
    if (!first.data) return;
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    setLoadingMore(true);
    setMoreError(null);
    try {
      const next = await api.similar(
        id, { filters, limit: PAGE_SIZE, offset: first.data.cards.length + more.length }, controller.signal,
      );
      setMore([...more, ...next.cards]);
      setHasMore(next.has_more);
    } catch (err) {
      if (!controller.signal.aborted) setMoreError(err instanceof ApiError ? err : new ApiError(0, null));
    } finally {
      if (!controller.signal.aborted) setLoadingMore(false);
    }
  }

  const cards = first.data ? [...first.data.cards, ...more] : [];
  const canShowMore = hasMore ?? first.data?.has_more ?? false;
  return (
    <section className="similar">
      <div className="similar-tools">
        <button type="button" className="btn" aria-expanded={open} aria-controls="similar-filters"
                onClick={() => setOpen(!open)}>
          Filter similar cards
        </button>
        {filters.length > 0 && (
          <span className="muted">{filters.length} {filters.length === 1 ? "filter" : "filters"} active</span>
        )}
      </div>
      {open && (
        <form id="similar-filters" className="adv-form" onSubmit={apply}>
          {rows.map((f, i) => (
            <FilterRow
              key={i}
              filter={f}
              index={i}
              onChange={(next) => setRows(rows.map((r, j) => (j === i ? next : r)))}
              onRemove={() => setRows(rows.filter((_, j) => j !== i))}
            />
          ))}
          <div className="actions">
            <button type="button" className="btn" disabled={rows.length >= MAX_FILTERS}
                    onClick={() => setRows([...rows, defaultFilter()])}>
              + Add filter
            </button>
            <button type="button" className="btn" onClick={() => setSearchParams(new URLSearchParams())}>
              Clear filters
            </button>
            <button type="submit" className="btn primary">Apply filters</button>
          </div>
        </form>
      )}

      {first.status === "loading" && <Loading />}
      {first.status === "error" && first.error && <SimilarError error={first.error} onRetry={first.reload} />}
      {first.status === "ok" && first.data && (
        cards.length === 0
          ? <p className="muted">{filters.length ? "No similar cards match these filters." : "No similar cards."}</p>
          : <CardGrid cards={cards} search={search} />
      )}
      {moreError && <ErrorState error={moreError} onRetry={showMore} />}
      {first.status === "ok" && canShowMore && !moreError && (
        <div className="actions">
          <button type="button" className="btn" disabled={loadingMore} onClick={showMore}>
            {loadingMore ? "Loading…" : "Show more"}
          </button>
        </div>
      )}
    </section>
  );
}

function SimilarError({ error, onRetry }: { error: ApiError; onRetry: () => void }) {
  if (error.status === 404 && error.detail !== "Card not found.") {
    return <p className="muted">Similar cards aren't available for this card yet</p>;
  }
  return <ErrorState error={error} onRetry={onRetry} />;
}
