import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { useSearchParams } from "react-router";
import { api } from "../api";
import CardGrid from "../components/CardGrid";
import ErrorState from "../components/ErrorState";
import FilterRow from "../components/FilterRow";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import { MAX_FILTERS, defaultFilter, parseSearchParams, toRequest, toSearchParams } from "../lib/searchFilters";
import type { Filter, Sort } from "../lib/searchFilters";
import { useAsync } from "../lib/useAsync";

const SORTS: { value: Sort; label: string }[] = [
  { value: "name", label: "Name" },
  { value: "cmc_asc", label: "Mana value ↑" },
  { value: "cmc_desc", label: "Mana value ↓" },
];

export default function AdvancedSearchPage() {
  const [searchParams] = useSearchParams();
  // key remounts the form when the URL changes (Back, shared link), so rows always match the results.
  return <SearchView key={searchParams.toString()} />;
}

function SearchView() {
  const [searchParams, setSearchParams] = useSearchParams();
  const applied = parseSearchParams(searchParams);
  const [filters, setFilters] = useState<Filter[]>(applied.filters);
  const [sort, setSort] = useState<Sort>(applied.sort);

  const request = toRequest(applied.filters, applied.sort);
  const results = useAsync(
    (s) => (request ? api.search(request, s) : Promise.resolve(null)),
    [searchParams.toString()],
  );

  useEffect(() => {
    document.title = "Advanced search";
  }, []);

  function submit(e: FormEvent) {
    e.preventDefault();
    setSearchParams(toSearchParams(filters, sort));
  }

  function update(i: number, filter: Filter) {
    setFilters(filters.map((f, j) => (j === i ? filter : f)));
  }

  const data = results.data;
  return (
    <Layout>
      <h1 className="page-title">Advanced search</h1>
      <form className="adv-form" onSubmit={submit}>
        {filters.map((f, i) => (
          <FilterRow
            key={i}
            filter={f}
            index={i}
            onChange={(next) => update(i, next)}
            onRemove={() => setFilters(filters.filter((_, j) => j !== i))}
          />
        ))}
        <div className="actions">
          <button
            type="button"
            className="btn"
            disabled={filters.length >= MAX_FILTERS}
            onClick={() => setFilters([...filters, defaultFilter()])}
          >
            + Add filter
          </button>
          <label className="sort">
            <span className="muted">Sort by</span>
            <select className="fld" value={sort} onChange={(e) => setSort(e.target.value as Sort)}>
              {SORTS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </label>
          <button type="submit" className="btn primary">
            Search
          </button>
        </div>
      </form>
      {!request && <p className="muted">Add at least one filter with a value, then press Search.</p>}
      {request && results.status === "loading" && <Loading />}
      {request && results.status === "error" && results.error && (
        <ErrorState error={results.error} onRetry={results.reload} />
      )}
      {request && results.status === "ok" && data && (
        data.total === 0 ? (
          <p className="muted">No cards match these filters.</p>
        ) : (
          <>
            <p className="muted count">
              {data.total} {data.total === 1 ? "card" : "cards"}{data.total > 200 ? " · showing the first 200" : ""}
            </p>
            <CardGrid cards={data.cards} />
          </>
        )
      )}
    </Layout>
  );
}
