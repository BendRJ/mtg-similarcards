import type { CardSummary } from "../types";
import CardTile from "./CardTile";

export default function CardGrid({ cards, search }: { cards: CardSummary[]; search?: string }) {
  return (
    <div className="grid">
      {cards.map((card) => (
        <CardTile key={card.id} card={card} search={search} />
      ))}
    </div>
  );
}
