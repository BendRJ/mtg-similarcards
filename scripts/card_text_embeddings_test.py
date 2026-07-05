from pathlib import Path
from app.services.vector_service import build_card_text
import json

SCHEMA_FILE = Path(__file__).parent.parent / "src" / "database" / "schemas" / "cards_creatures.json"

with open(SCHEMA_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)

    texts = build_card_text(data)
    print(texts)