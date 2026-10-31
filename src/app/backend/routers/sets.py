from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.backend import queries
from app.backend.db import get_db_cursor
from app.backend.models import CardSummary, SetSummary

router = APIRouter(prefix="/sets", tags=["sets"])


@router.get("", response_model=list[SetSummary],
            description="Sets that have cards loaded, newest first.")
def list_sets(cur: queries.Cursor = Depends(get_db_cursor)):
    return queries.list_sets(cur)


@router.get("/{set_code}/cards", response_model=list[CardSummary],
            description="A set's cards in collector order, one entry per card.")
def get_set_cards(set_code: str,
                  colors: str | None = Query(None, pattern=r"^[WUBRGC](,[WUBRGC])*$",
                                             description="Any of W,U,B,R,G,C (C = colorless), comma-separated."),
                  cur: queries.Cursor = Depends(get_db_cursor)):
    if not queries.set_exists(cur, set_code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Set not found.")
    return queries.get_set_cards(cur, set_code, colors.split(",") if colors else None)
