"""
Pydantic schema validation of API responses.
"""
from pydantic import BaseModel


class SetsValidation(BaseModel):
    # from create table statement
    # code TEXT PRIMARY KEY,
    # name TEXT NOT NULL,
    # set_type TEXT,
    # released_at DATE,
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
    nonfoil_only: bool
    icon_svg_uri: str

    model_config = {
        "extra": "ignore"  # Ignore all other fields in response body not specified above
    }


class CardsValidation(BaseModel):
    pass