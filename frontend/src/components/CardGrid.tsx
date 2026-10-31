import type { CardSummary } from "../types";
import CardTile from "./CardTile";

export default function CardGrid({ cards }: { cards: CardSummary[] }) {
  return (
    <div className="grid">
      {cards.map((card) => (
        <CardTile key={card.id} card={card} />
      ))}
    </div>
  );
}
