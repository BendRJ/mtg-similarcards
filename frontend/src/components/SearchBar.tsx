import { useEffect, useId, useRef, useState } from "react";
import type { KeyboardEvent } from "react";
import { useNavigate } from "react-router";
import { api } from "../api";
import { matchSets } from "../lib/sets";
import type { AutocompleteCard, SetSummary } from "../types";

const MIN_CHARS = 2;
const DEBOUNCE_MS = 150;

type SearchBarProps = {
  size?: "normal" | "big";
  autoFocus?: boolean;
};

type Results = { query: string; cards: AutocompleteCard[]; sets: SetSummary[]; unreachable: boolean };

type Row =
  | { kind: "card"; card: AutocompleteCard }
  | { kind: "set"; set: SetSummary };

// Small Scryfall image for the 26px thumbnail; the normal one only when there is no small.
function thumbnail(card: AutocompleteCard): string | null {
  return card.image_url_small ?? card.image_url;
}

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
  const pendingEnter = useRef(false);
  const trimmed = query.trim();

  useEffect(() => {
    if (trimmed.length < MIN_CHARS) {
      setResults(null);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      let failures = 0;
      const [cards, allSets] = await Promise.all([
        api.autocomplete(trimmed, 10, controller.signal).catch((): AutocompleteCard[] => {
          failures += 1;
          return [];
        }),
        api.sets(controller.signal).catch((): SetSummary[] => {
          failures += 1;
          return [];
        }),
      ]);
      if (controller.signal.aborted) return;
      setResults({ query: trimmed, cards, sets: matchSets(allSets, trimmed), unreachable: failures === 2 });
      setActive(-1);
    }, DEBOUNCE_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [trimmed]);

  useEffect(() => {
    function onPointerDown(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, []);

  // Results can lag behind the typed text; only act on them (Enter, arrows) once they match it.
  const fresh = results !== null && results.query === trimmed;
  const rows = results ? toRows(results) : [];
  const actionableRows = fresh ? rows : [];
  const showDropdown = open && results !== null;

  useEffect(() => {
    if (pendingEnter.current && fresh && rows.length > 0) {
      pendingEnter.current = false;
      go(rows[0]);
    }
  });

  function go(row: Row) {
    navigate(row.kind === "card" ? `/card/${encodeURIComponent(row.card.id)}` : `/set/${encodeURIComponent(row.set.code)}`);
    setOpen(false);
    setQuery("");
    setActive(-1);
    pendingEnter.current = false;
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      setOpen(false);
    } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (actionableRows.length === 0) return;
      e.preventDefault();
      setOpen(true);
      const n = actionableRows.length;
      const step = e.key === "ArrowDown" ? 1 : -1;
      setActive((a) => (a === -1 ? (step === 1 ? 0 : n - 1) : (a + step + n) % n));
    } else if (e.key === "Enter") {
      if (fresh && showDropdown && rows.length > 0) {
        e.preventDefault();
        go(rows[active >= 0 ? active : 0]);
      } else if (!fresh && trimmed.length >= MIN_CHARS) {
        e.preventDefault();
        pendingEnter.current = true;
      }
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
          thumbnail(row.card) ? (
            <img className="thumb" src={thumbnail(row.card)!} alt="" loading="lazy" />
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
          setActive(-1);
          pendingEnter.current = false;
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />
      {showDropdown ? (
        <ul className="dropdown" id={listId} role="listbox">
          {rows.length === 0 ? (
            <li role="presentation" className="dd-empty">
              {results?.unreachable ? "Couldn't reach the card database. Try again." : "No cards or sets found"}
            </li>
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
