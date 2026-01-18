"""
Module for API endpoint configurations
"""

class APIEndpoints:
    """
    Docstring for APIEndpoints
    """
    BASE_URL = "https://api.magicthegathering.io/v1"
    CARDS_ENDPOINT = f"{BASE_URL}/cards"
    CARDS_ENDPOINT_IDSEARCH = f"{CARDS_ENDPOINT}/{{card_id}}"
    SETS_ENDPOINT = f"{BASE_URL}/sets"
    SETS_ENDPOINT_CODESEARCH = f"{SETS_ENDPOINT}/{{set_code}}"

    @staticmethod
    def get_card_url(card_id: str) -> str:
        """
        Construct URL for specific card lookup
        
        Args:
            card_id: The card ID to look up
            
        Returns:
            Complete URL for card endpoint
        """
        return APIEndpoints.CARDS_ENDPOINT_IDSEARCH.format(card_id=card_id)
    
    @staticmethod
    def get_set_url(set_code: str) -> str:
        """
        Construct URL for specific set lookup
        
        Args:
            set_code: The set code to look up
            
        Returns:
            Complete URL for set endpoint
        """
        return APIEndpoints.SETS_ENDPOINT_CODESEARCH.format(set_code=set_code)
    