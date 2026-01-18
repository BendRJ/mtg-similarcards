
class APIEndpoints:
    BASE_URL = "https://api.magicthegathering.io/v1"
    CARDS_ENDPOINT = f"{BASE_URL}/cards"
    CARDS_ENDPOINT_IDSEARCH = f"{CARDS_ENDPOINT}/{{card_id}}"
    SETS_ENDPOINT = f"{BASE_URL}/sets"
    SETS_ENDPOINT_CODESEARCH = f"{SETS_ENDPOINT}/{{set_code}}"