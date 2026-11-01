import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";
import { api } from "../api";
import ErrorState from "../components/ErrorState";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import SimilarCards from "../components/SimilarCards";
import { filtersQuery } from "../lib/searchFilters";
import { useAsync } from "../lib/useAsync";
import type { CardDetail, Printing } from "../types";
import NotFoundPage from "./NotFoundPage";

export default function CardPage() {
  const { id = "" } = useParams();
  // key remounts the view on route change, so old data can never show next to the new id
  return <CardView key={id} id={id} />;
}

function CardView({ id }: { id: string }) {
  const card = useAsync((s) => api.card(id, s), [id]);
  const printings = useAsync((s) => api.printings(id, s), [id]);
  const [searchParams] = useSearchParams();
  // Printing links keep the similar-cards filters, so switching printings doesn't lose them.
  const search = filtersQuery(searchParams);

  const name = card.data?.name;
  useEffect(() => {
    if (name) document.title = name;
  }, [name]);

  if (card.status === "error" && card.error?.status === 404) {
    return <NotFoundPage message="Card not found" />;
  }

  return (
    <Layout>
      {card.status === "loading" && <Loading />}
      {card.status === "error" && card.error && <ErrorState error={card.error} onRetry={card.reload} />}
      {card.status === "ok" && card.data && <Detail card={card.data} />}

      <h2>Printings</h2>
      {printings.status === "loading" && <Loading />}
      {printings.status === "error" && printings.error && (
        <ErrorState error={printings.error} onRetry={printings.reload} />
      )}
      {printings.status === "ok" && printings.data && (
        <div className="printings">
          {printings.data.map((p) => (
            <PrintingItem key={p.id} printing={p} current={p.id === id} search={search} />
          ))}
        </div>
      )}

      <h2>Similar cards</h2>
      <SimilarCards id={id} />
    </Layout>
  );
}

function Detail({ card }: { card: CardDetail }) {
  const [failed, setFailed] = useState(false);
  const imageSrc = card.image_url_large ?? card.image_url;
  const showImage = imageSrc !== null && !failed;
  const setLine = [
    card.set_name,
    card.collector_number ? `#${card.collector_number}` : null,
    card.rarity,
  ].filter(Boolean).join(" · ");
  const stats = card.power !== null && card.toughness !== null
    ? `${card.power}/${card.toughness}`
    : card.loyalty !== null ? `Loyalty ${card.loyalty}` : null;
  return (
    <div className="detail">
      {showImage ? (
        <img className="detail-image" src={imageSrc!} alt={card.name} onError={() => setFailed(true)} />
      ) : (
        <div className="detail-image tile-placeholder">{card.name}</div>
      )}
      <div className="detail-text">
        <h1>
          {card.name} {card.mana_cost && <span className="mana">{card.mana_cost}</span>}
        </h1>
        {card.type_line && <p>{card.type_line}</p>}
        {setLine && <p className="muted">{setLine}</p>}
        {card.artist && <p className="muted">Artist: {card.artist}</p>}
        {card.oracle_text && <p className="oracle">{card.oracle_text}</p>}
        {stats && <p><strong>{stats}</strong></p>}
      </div>
    </div>
  );
}

function PrintingItem({ printing, current, search }: { printing: Printing; current: boolean; search: string }) {
  const year = printing.released_at?.slice(0, 4);
  const label = [printing.set_code?.toUpperCase(), year].filter(Boolean).join(" ") || "Printing";
  return (
    <Link
      to={`/card/${encodeURIComponent(printing.id)}${search}`}
      className={current ? "printing sel" : "printing"}
      aria-current={current ? "true" : undefined}
    >
      {label}
    </Link>
  );
}
