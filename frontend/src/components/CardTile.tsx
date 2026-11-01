import { useState } from "react";
import { Link } from "react-router";
import type { CardSummary } from "../types";

// search: an optional "?…" query carried onto the card link (e.g. the similar-cards filters).
export default function CardTile({ card, search = "" }: { card: CardSummary; search?: string }) {
  const [failed, setFailed] = useState(false);
  const showImage = card.image_url !== null && !failed;
  return (
    <Link to={`/card/${encodeURIComponent(card.id)}${search}`} className="tile">
      {showImage ? (
        <img src={card.image_url!} alt={card.name} loading="lazy" onError={() => setFailed(true)} />
      ) : (
        <div className="tile-placeholder">{card.name}</div>
      )}
    </Link>
  );
}
