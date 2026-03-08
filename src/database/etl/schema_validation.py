"""
Pydantic schema validation of API responses.
"""
from typing import Any

from pydantic import BaseModel, Field


class SetsValidation(BaseModel):
    """
    Validation of API response for sets endpoint.
    Should match the columns defined in sets.sql and the fields in the upsert query.
    Any fields in the API response not defined here will be ignored due to model_config.
    """
    code: str
    name: str
    set_type: str | None = None
    released_at: str
    card_count: int | None = None
    search_uri: str
    digital: bool = False
    foil_only: bool = False
    nonfoil_only: bool = False
    icon_svg_uri: str | None = None

    model_config = {
        "extra": "ignore"  # Ignore all other fields in response body not specified above
    }

class CardsValidation(BaseModel):
    """
    Validation of API response for cards endpoint.
    Should match the columns defined in cards.sql and the fields in the upsert query.
    Any fields in the API response not defined here will be ignored due to model_config.
    """

    # Identity
    id: str
    oracle_id: str | None = None
    name: str
    lang: str | None = None
    released_at: str | None = None
    layout: str | None = None

    # Mana & Cost
    mana_cost: str | None = None
    cmc: float | None = None

    # Type & Rules
    type_line: str | None = None
    oracle_text: str | None = None
    flavor_text: str | None = None

    # Combat Stats (creatures)
    power: str | None = None
    toughness: str | None = None

    # Planeswalker
    loyalty: str | None = None

    # Colors & Keywords
    colors: list[str] | None = None
    color_identity: list[str] | None = None
    keywords: list[str] | None = None
    produced_mana: list[str] | None = None

    # Related Cards (tokens, combo pieces)
    all_parts: list[dict[str, Any]] | None = None

    # Legality & Availability
    legalities: dict[str, str] | None = None
    games: list[str] | None = None
    reserved: bool = False
    foil: bool = False
    nonfoil: bool = False
    finishes: list[str] | None = None

    # Set Info
    set_code: str | None = Field(default=None, validation_alias="set") #api returns set code as "set", but we want to use set_code as col name
    set_name: str | None = None
    set_type: str | None = None
    collector_number: str | None = None
    digital: bool = False
    rarity: str | None = None

    # Card Properties
    oversized: bool = False
    promo: bool = False
    promo_types: list[str] | None = None
    reprint: bool = False
    variation: bool = False
    booster: bool = False
    full_art: bool = False
    textless: bool = False
    story_spotlight: bool = False

    # Visual & Frame
    border_color: str | None = None
    frame: str | None = None
    frame_effects: list[str] | None = None
    security_stamp: str | None = None
    highres_image: bool = False
    image_status: str | None = None
    image_uris: dict[str, str] | None = None

    # Artist
    artist: str | None = None

    # Rankings
    edhrec_rank: int | None = None
    penny_rank: int | None = None

    # Pricing
    prices: dict[str, str | None] | None = None

    model_config = {
        "extra": "ignore"
    }
