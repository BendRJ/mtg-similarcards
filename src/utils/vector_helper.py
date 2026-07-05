"""
Support functions for vector service and training ML model.
Provides functions to:
- Build text representations of cards for embedding
"""
from typing import Any

def build_card_text(card: dict[str, Any]) -> str:
    """Assemble a text representation of a card for embedding.

    Combines the most semantically relevant fields into a single string.

    Args:
        card: A dict with card column values (from a DB row or similar).
    """
    parts: list[str] = []

    if type_line := card.get("type_line"):
        parts.append(f"{type_line}\n")

    if oracle_text := card.get("oracle_text"):
        parts.append(oracle_text)

    # keywords is part of oracle text, might confuse the algo
    # if keywords := card.get("keywords"):
    #     if isinstance(keywords, list) and keywords:
    #         parts.append(f"Keywords: {', '.join(keywords)}")

    if colors := card.get("colors"):
        if isinstance(colors, list) and colors:
            parts.append(f"\nColors: {', '.join(colors)}")

    return "".join(parts)