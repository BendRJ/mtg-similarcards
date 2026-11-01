import { COLORS } from "../lib/colors";
import type { Color } from "../lib/colors";
import { FIELDS, TYPES, defaultFilter, valueKind } from "../lib/searchFilters";
import type { Field, Filter, Op } from "../lib/searchFilters";

type FilterRowProps = {
  filter: Filter;
  index: number;
  onChange: (filter: Filter) => void;
  onRemove: () => void;
};

export default function FilterRow({ filter, index, onChange, onRemove }: FilterRowProps) {
  const kind = valueKind(filter.field, filter.op);
  const colors = Array.isArray(filter.value) ? filter.value : [];
  const text = typeof filter.value === "string" ? filter.value : "";

  function changeOp(op: Op) {
    // Switching between the type list and a text box must not carry the old value over.
    const reset = valueKind(filter.field, op) !== kind;
    onChange({ ...filter, op, value: reset ? "" : filter.value });
  }

  function toggle(color: Color) {
    const next = colors.includes(color) ? colors.filter((c) => c !== color) : [...colors, color];
    onChange({ ...filter, value: COLORS.filter((c) => next.includes(c)) });
  }

  return (
    <div className="filter-row">
      <span className="and">{index > 0 ? "and" : ""}</span>
      <select
        className="fld"
        aria-label="Field"
        value={filter.field}
        onChange={(e) => onChange(defaultFilter(e.target.value as Field))}
      >
        {(Object.keys(FIELDS) as Field[]).map((f) => (
          <option key={f} value={f}>{FIELDS[f].label}</option>
        ))}
      </select>
      <select className="fld" aria-label="Condition" value={filter.op} onChange={(e) => changeOp(e.target.value as Op)}>
        {FIELDS[filter.field].ops.map((o) => (
          <option key={o.op} value={o.op}>{o.label}</option>
        ))}
      </select>
      {kind === "text" && (
        <input
          className="fld inp"
          type="text"
          aria-label="Value"
          maxLength={100}
          value={text}
          onChange={(e) => onChange({ ...filter, value: e.target.value })}
        />
      )}
      {kind === "type" && (
        <select className="fld" aria-label="Value" value={text} onChange={(e) => onChange({ ...filter, value: e.target.value })}>
          <option value="">Choose a type</option>
          {TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      )}
      {kind === "colors" && (
        <div className="chips filter-chips">
          {COLORS.map((c) => (
            <button
              key={c}
              type="button"
              className={colors.includes(c) ? "chip on" : "chip"}
              aria-pressed={colors.includes(c)}
              onClick={() => toggle(c)}
            >
              {c}
            </button>
          ))}
        </div>
      )}
      <button type="button" className="remove" aria-label="Remove filter" onClick={onRemove}>
        ✕
      </button>
    </div>
  );
}
