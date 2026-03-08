"""
Pydantic schema validation of API responses.
"""
from pydantic import BaseModel


class SetsValidation(BaseModel):
    """
    Validation of API response for sets endpoint.
    Should match the columns defined in sets.sql and the fields in the upsert query.
    Any fields in the API response not defined here will be ignored due to model_config.
    """
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
