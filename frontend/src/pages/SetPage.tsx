import { useEffect } from "react";
import { useParams, useSearchParams } from "react-router";
import { api } from "../api";
import CardGrid from "../components/CardGrid";
import ErrorState from "../components/ErrorState";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import { COLORS, parseColorList, serializeColors } from "../lib/colors";
import type { Color } from "../lib/colors";
import { useAsync } from "../lib/useAsync";
import NotFoundPage from "./NotFoundPage";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

// Reads the "YYYY-MM-DD" parts directly; new Date(str) is UTC midnight and can shift the month.
function monthYear(releasedAt: string | null): string | null {
  const m = releasedAt?.match(/^(\d{4})-(\d{2})/);
  if (!m) return null;
  const month = MONTHS[Number(m[2]) - 1];
  return month ? `${month} ${m[1]}` : null;
}

export default function SetPage() {
  const { code = "" } = useParams();
  // key remounts the view on route change, so old data can never show next to the new code
  return <SetView key={code} code={code} />;
}

function SetView({ code }: { code: string }) {
  const [searchParams, setSearchParams] = useSearchParams();
  const colors = parseColorList(searchParams.get("colors"));
  const cards = useAsync((s) => api.setCards(code, colors, s), [code, serializeColors(colors)]);
  // The header is optional: if /sets fails or lacks this set, only the code is shown.
  const sets = useAsync((s) => api.sets(s), []);

  const upper = code.toUpperCase();
  const info = sets.data?.find((x) => x.code.toLowerCase() === code.toLowerCase());
  const name = info?.name;
  const date = monthYear(info?.released_at ?? null);

  useEffect(() => {
    if (name) document.title = name;
  }, [name]);

  function toggle(color: Color) {
    const next = colors.includes(color) ? colors.filter((c) => c !== color) : [...colors, color];
    const params = new URLSearchParams(searchParams);
    if (next.length) params.set("colors", serializeColors(next));
    else params.delete("colors");
    setSearchParams(params, { replace: true });
  }

  if (cards.status === "error" && cards.error?.status === 404) {
    return <NotFoundPage message="Set not found" />;
  }

  return (
    <Layout>
      <div className="toolbar">
        <h1>{name ?? upper}</h1>
        {name && (
          <span className="muted">{[upper, date].filter(Boolean).join(" · ")}</span>
        )}
        <div className="chips">
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
      </div>
      {cards.status === "loading" && <Loading />}
      {cards.status === "error" && cards.error && <ErrorState error={cards.error} onRetry={cards.reload} />}
      {cards.status === "ok" && cards.data && <CardGrid cards={cards.data} />}
    </Layout>
  );
}
