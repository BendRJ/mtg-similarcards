import { useState } from "react";
import { Link } from "react-router";
import type { CardSummary } from "../types";

export default function CardTile({ card }: { card: CardSummary }) {
  const [failed, setFailed] = useState(false);
  const showImage = card.image_url !== null && !failed;
  return (
    <Link to={`/card/${encodeURIComponent(card.id)}`} className="tile">
      {showImage ? (
        <img src={card.image_url!} alt={card.name} loading="lazy" onError={() => setFailed(true)} />
      ) : (
        <div className="tile-placeholder">{card.name}</div>
      )}
    </Link>
  );
}
