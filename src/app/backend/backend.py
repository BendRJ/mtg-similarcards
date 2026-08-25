from fastapi import FastAPI, HTTPException, status
from app.backend.utils.database import cards

app = FastAPI()

@app.get("/", name="Hello World", include_in_schema=False)
def home():
    return {"hello":"World!"}

@app.get("/cards")
def get_cards():
    return cards

@app.get("/cards/{card_id}", description="Endpoint for retrieving individual cards from Database.")
def get_card(card_id: str):
    for card in cards:
        if card.get("id") == card_id:
            return card
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND
                        , detail="Card does not exist in DB or wrong ID provided.")