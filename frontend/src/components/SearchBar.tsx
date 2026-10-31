import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { useNavigate } from "react-router";
import { api } from "../api";
import { matchSets } from "../lib/sets";
import type { CardSummary, SetSummary } from "../types";

const MIN_CHARS = 2;
const DEBOUNCE_MS = 150;

type SearchBarProps = {
  size?: "normal" | "big";
  autoFocus?: boolean;
};

type Results = { cards: CardSummary[]; sets: SetSummary[] };

type Row =
  | { kind: "card"; card: CardSummary }
  | { kind: "set"; set: SetSummary };

function toRows({ cards, sets }: Results): Row[] {
  return [
    ...cards.map((card): Row => ({ kind: "card", card })),
    ...sets.map((set): Row => ({ kind: "set", set })),
  ];
}

export default function SearchBar({ size = "normal", autoFocus = false }: SearchBarProps) {
  const navigate = useNavigate();
  const listId = useId();
  const containerRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Results | null>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);

  useEffect(() => {
    if (query.trim().length < MIN_CHARS) {
      setResults(null);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      const [cards, allSets] = await Promise.all([
        api.autocomplete(query, 10, controller.signal).catch((): CardSummary[] => []),
        api.sets(controller.signal).catch((): SetSummary[] => []),
      ]);
      if (controller.signal.aborted) return;
      setResults({ cards, sets: matchSets(allSets, query) });
      setActive(-1);
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  useEffect(() => {
    function onPointerDown(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  const rows = results ? toRows(results) : [];
  const showDropdown = open && results !== null;

  function go(row: Row) {
    navigate(row.kind === "card" ? `/card/${encodeURIComponent(row.card.id)}` : `/set/${encodeURIComponent(row.set.code)}`);
    setOpen(false);
    setQuery("");
    setActive(-1);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      setOpen(false);
    } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (rows.length === 0) return;
      e.preventDefault();
      setOpen(true);
      const step = e.key === "ArrowDown" ? 1 : -1;
      setActive((a) => (a === -1 ? (step === 1 ? 0 : rows.length - 1) : (a + step + rows.length) % rows.length));
    } else if (e.key === "Enter" && showDropdown && rows.length > 0) {
      e.preventDefault();
      go(rows[active >= 0 ? active : 0]);
    }
  }

  function renderRow(row: Row, index: number) {
    const id = `${listId}-${index}`;
    const isCard = row.kind === "card";
    return (
      <li
        key={id}
        id={id}
        role="option"
        aria-selected={index === active}
        className={`dd-row${index === active ? " active" : ""}`}
        onMouseDown={(e) => e.preventDefault()}
        onMouseEnter={() => setActive(index)}
        onClick={() => go(row)}
      >
        {row.kind === "card" ? (
          row.card.image_url ? (
            <img className="thumb" src={row.card.image_url} alt="" loading="lazy" />
          ) : (
            <span className="thumb" />
          )
        ) : row.set.icon_svg_uri ? (
          <img className="seticon" src={row.set.icon_svg_uri} alt="" loading="lazy" />
        ) : (
          <span className="seticon" />
        )}
        <span className="dd-name">{isCard ? row.card.name : row.set.name}</span>
        <span className="meta">
          {row.kind === "card"
            ? `${row.card.type_line ?? ""} · ${(row.card.set_code ?? "").toUpperCase()}`
            : `${row.set.code.toUpperCase()} · ${row.set.released_at?.slice(0, 4) ?? ""}`}
        </span>
      </li>
    );
  }

  const cardCount = results?.cards.length ?? 0;

  return (
    <div className={`search search-${size}`} ref={containerRef}>
      <input
        className="search-input"
        type="text"
        role="combobox"
        aria-expanded={showDropdown}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={showDropdown && active >= 0 ? `${listId}-${active}` : undefined}
        placeholder="Search cards or sets…"
        autoComplete="off"
        autoFocus={autoFocus}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />
      {showDropdown ? (
        <ul className="dropdown" id={listId} role="listbox">
          {rows.length === 0 ? (
            <li role="presentation" className="dd-empty">No cards or sets found</li>
          ) : (
            <>
              {cardCount > 0 ? <li role="presentation" className="dd-group">Cards</li> : null}
              {rows.slice(0, cardCount).map((row, i) => renderRow(row, i))}
              {rows.length > cardCount ? <li role="presentation" className="dd-group">Sets</li> : null}
              {rows.slice(cardCount).map((row, i) => renderRow(row, cardCount + i))}
            </>
          )}
        </ul>
      ) : null}
    </div>
  );
}
