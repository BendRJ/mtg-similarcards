"""Response models: the public contract of the backend-for-frontend.

Deliberately narrower than the cards table. Add a field here only when a screen needs it.
"""

import datetime

from pydantic import BaseModel


class CardSummary(BaseModel):
    """One card tile or autocomplete row."""
    id: str
    name: str
    mana_cost: str | None = None
    type_line: str | None = None
    colors: list[str] | None = None
    rarity: str | None = None
    set_code: str | None = None
    image_url: str | None = None


class CardDetail(CardSummary):
    oracle_id: str | None = None
    cmc: float | None = None
    oracle_text: str | None = None
    flavor_text: str | None = None
    power: str | None = None
    toughness: str | None = None
    loyalty: str | None = None
    keywords: list[str] | None = None
    color_identity: list[str] | None = None
    set_name: str | None = None
    collector_number: str | None = None
    released_at: datetime.date | None = None
    artist: str | None = None
    legalities: dict[str, str] | None = None
    image_url_large: str | None = None


class Printing(BaseModel):
    id: str
    set_code: str | None = None
    set_name: str | None = None
    collector_number: str | None = None
    released_at: datetime.date | None = None
    rarity: str | None = None
    image_url: str | None = None


class SimilarCard(CardSummary):
    # Cosine distance to the reference card, lower = more similar.
    distance: float


class SetSummary(BaseModel):
    code: str
    name: str
    released_at: str | None = None
    set_type: str | None = None
    card_count: int | None = None
    icon_svg_uri: str | None = None
