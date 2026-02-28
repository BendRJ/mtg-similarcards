"""
Pydantic schema validation of API responses.
"""
from pydantic import BaseModel


class SetsValidation(BaseModel):
    """
    Validation of API response for sets endpoint.
    """
    # from create table statement
    # code TEXT PRIMARY KEY,
    # name TEXT NOT NULL,
    # set_type TEXT,
    # released_at TEXT,
    # card_count INTEGER,
    # digital BOOLEAN NOT NULL DEFAULT FALSE,
    # foil_only BOOLEAN NOT NULL DEFAULT FALSE,
    # nonfoil_only BOOLEAN NOT NULL DEFAULT FALSE,
    # icon_svg_uri TEXT
    code: str
    name: str
    set_type: str
    released_at: str
    card_count: int
    search_uri: str
    digital: bool
    foil_only: bool = False
    nonfoil_only: bool = False
    icon_svg_uri: str

    model_config = {
        "extra": "ignore"  # Ignore all other fields in response body not specified above
    }


class CardsValidation(BaseModel):
    """
    Validation of API response for cards endpoint.
    """

