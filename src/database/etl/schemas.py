from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class SetsIngest(BaseModel):
    object: str
    id: str
    price: Decimal = Field(gt=0)
    created_at: datetime

    model_config = {
        "extra": "ignore"  # Ignore fields we don't care about
    }