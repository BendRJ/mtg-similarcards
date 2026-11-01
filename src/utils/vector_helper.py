"""
Support functions for vector service and training ML model.
Provides functions to:
- Build text representations of cards for embedding
"""
from typing import Any

def build_card_text(card: dict[str, Any]) -> str:
    """Assemble the text that is embedded for "similar by text".

    The rules text, or the keywords for cards without one (multi-part cards keep their
    rules text on the faces, which aren't stored). Type line and colors are left out on
    purpose: similarity should follow what a card does, and colors combine freely.

    Args:
        card: A dict with card column values (from a DB row or similar).

    Returns:
        The text to embed, or "" when the card has neither rules text nor keywords.
    """
    if oracle_text := card.get("oracle_text"):
        return oracle_text
    keywords = card.get("keywords")
    if isinstance(keywords, list) and keywords:
        return ", ".join(keywords)
    return ""
