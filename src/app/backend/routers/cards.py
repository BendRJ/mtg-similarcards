from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.backend import queries
from app.backend.db import get_db_cursor
from app.backend.models import CardDetail, CardSummary, Printing

router = APIRouter(prefix="/cards", tags=["cards"])

# Static paths like /cards/autocomplete must be declared above /{card_id},
# or FastAPI matches them as a card id.


@router.get("/autocomplete", response_model=list[CardSummary],
            description="Name suggestions while typing, one entry per card.")
def autocomplete(q: str = Query(min_length=2),
                 limit: int = Query(10, ge=1, le=25),
                 cur: queries.Cursor = Depends(get_db_cursor)):
    return queries.autocomplete_cards(cur, q, limit)


@router.get("/{card_id}", response_model=CardDetail,
            description="One printing of a card, by its Scryfall id.")
def get_card(card_id: str, cur: queries.Cursor = Depends(get_db_cursor)):
    card = queries.get_card(cur, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found.")
    return card


@router.get("/{card_id}/printings", response_model=list[Printing],
            description="Every printing of the same card, newest first.")
def get_printings(card_id: str, cur: queries.Cursor = Depends(get_db_cursor)):
    printings = queries.get_printings(cur, card_id)
    # The card itself is always one of its printings, so empty means unknown id.
    if not printings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found.")
    return printings
