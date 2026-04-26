from app.services.vector_service import build_card_text
import json

with open("src/database/schemas/cards_creatures.json", "r" ,encoding="utf-8") as file:
    data = json.load(file)

    texts = build_card_text(data)
    print(texts)