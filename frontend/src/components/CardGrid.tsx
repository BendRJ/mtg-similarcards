import type { CardSummary } from "../types";
import CardTile from "./CardTile";

export default function CardGrid({ cards, className }: { cards: CardSummary[]; className?: string }) {
  return (
    <div className={className ? `grid ${className}` : "grid"}>
      {cards.map((card) => (
        <CardTile key={card.id} card={card} />
      ))}
    </div>
  );
}
