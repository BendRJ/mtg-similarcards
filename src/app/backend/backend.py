from fastapi import FastAPI
from app.backend.utils.database import cards

app = FastAPI()

@app.get("/")
def home():
    return {"hello":"World!"}

@app.get("/cards")
def get_cards():
    return cards