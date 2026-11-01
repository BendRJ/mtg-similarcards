from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.backend import queries
from app.backend.db import get_db_cursor
from app.backend.models import (AutocompleteCard, CardDetail, CardSummary, Printing, SearchRequest,
                                SearchResponse, SimilarCard)

router = APIRouter(prefix="/cards", tags=["cards"])

# Static paths like /cards/autocomplete and /cards/random must be declared above /{card_id},
# or FastAPI matches them as a card id.


@router.get("/autocomplete", response_model=list[AutocompleteCard],
            description="Name suggestions while typing, one entry per card.")
def autocomplete(q: str = Query(min_length=2),
                 limit: int = Query(10, ge=1, le=25),
                 cur: queries.Cursor = Depends(get_db_cursor)):
    return queries.autocomplete_cards(cur, q, limit)


@router.get("/random", response_model=list[CardSummary],
            description="Random cards having any of the given colors, one entry per card.")
def random_cards(colors: str = Query(pattern=r"^[WUBRGC](,[WUBRGC])*$",
                                     description="Any of W,U,B,R,G,C (C = colorless), comma-separated."),
                 limit: int = Query(100, ge=1, le=100),
                 cur: queries.Cursor = Depends(get_db_cursor)):
    return queries.random_cards(cur, colors.split(","), limit)


@router.post("/search", response_model=SearchResponse,
             description="Cards matching every filter, one entry per card (latest printing), at most 200.")
def search(req: SearchRequest, cur: queries.Cursor = Depends(get_db_cursor)):
    return queries.search_cards(cur, [f.model_dump() for f in req.filters], req.sort)


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


@router.get("/{card_id}/similar", response_model=list[SimilarCard],
            description="Most similar other cards by rules text, one entry per card, closest first.")
def get_similar(card_id: str,
                limit: int = Query(12, ge=1, le=50),
                cur: queries.Cursor = Depends(get_db_cursor)):
    if queries.get_card(cur, card_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found.")
    similar = queries.similar_cards(cur, card_id, limit)
    if similar is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No embedding for this card yet.")
    return similar


# Images of a printing never change, so browsers may cache them for a year.
IMAGE_HEADERS = {"Cache-Control": "public, max-age=31536000, immutable",
                 "X-Content-Type-Options": "nosniff"}


@router.get("/{card_id}/image", response_class=Response,
            responses={200: {"content": {"image/jpeg": {}}}},
            description="The stored image of one printing.")
def get_image(card_id: str, cur: queries.Cursor = Depends(get_db_cursor)):
    image = queries.get_card_image(cur, card_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No image stored for this card.")
    return Response(content=bytes(image["image"]),
                    media_type=image["content_type"] or "image/jpeg",
                    headers=IMAGE_HEADERS)
