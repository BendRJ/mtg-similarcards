"""Response models: the public contract of the backend-for-frontend.

Deliberately narrower than the cards table. Add a field here only when a screen needs it.
"""

import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.backend.queries import SEARCH_TYPES


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


class AutocompleteCard(CardSummary):
    # Scryfall's small image (146x204), enough for a dropdown thumbnail.
    image_url_small: str | None = None


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


# Advanced search. queries.search_cards trusts its input, so everything is checked here.
TEXT_OPS = ("contains", "not_contains")
SEARCH_OPS = {
    "oracle_text": TEXT_OPS,
    "name": TEXT_OPS,
    "keywords": TEXT_OPS,
    "type": ("is", "is_not") + TEXT_OPS,
    "colors": ("any", "all", "none"),
}
COLOR_ORDER = "WUBRGC"


class SearchFilter(BaseModel):
    field: Literal["oracle_text", "name", "keywords", "type", "colors"]
    op: str
    value: str | list[str]

    @model_validator(mode="after")
    def check_and_normalise(self):
        if self.op not in SEARCH_OPS[self.field]:
            raise ValueError(f"Operator {self.op!r} is not valid for field {self.field!r}.")
        if self.field == "colors":
            if not isinstance(self.value, list):
                raise ValueError("Colors need a list of letters.")
            letters = {c.strip().upper() for c in self.value}
            if not letters or not letters <= set(COLOR_ORDER):
                raise ValueError("Colors must be 1-6 distinct letters from W U B R G C.")
            self.value = [c for c in COLOR_ORDER if c in letters]
            return self
        if not isinstance(self.value, str):
            raise ValueError("This field needs a text value.")
        text = self.value.strip()
        if self.field == "type" and self.op in ("is", "is_not"):
            # Case-insensitive, normalised to the canonical name.
            canonical = {t.lower(): t for t in SEARCH_TYPES}.get(text.lower())
            if canonical is None:
                raise ValueError(f"Type must be one of: {', '.join(SEARCH_TYPES)}.")
            text = canonical
        elif not 1 <= len(text) <= 100:
            raise ValueError("Text must be 1-100 characters.")
        self.value = text
        return self


class SearchRequest(BaseModel):
    filters: list[SearchFilter] = Field(min_length=1, max_length=20)
    sort: Literal["name", "cmc_asc", "cmc_desc"] = "name"


class SearchResponse(BaseModel):
    # total is the full match count, cards holds at most 200.
    total: int
    cards: list[CardSummary]
