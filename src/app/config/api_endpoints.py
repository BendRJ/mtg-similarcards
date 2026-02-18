"""
Module for API endpoint configurations
"""

from typing import Optional

class APIEndpointsConfig:
    """
    Storage class for API endpoint URLs
    """
    BASE_URL = "https://api.magicthegathering.io/v1"
    CARDS_ENDPOINT = f"{BASE_URL}/cards"
    SETS_ENDPOINT = f"{BASE_URL}/sets"

    @staticmethod
    def get_card_url(card_id: Optional[str] = None,
                     set_code: Optional[str] = None,
                     rarity: Optional[str] = None,
                     page: Optional[int] = None,
                     pageSize: Optional[int] = None) -> str:
        """
        Construct URL for specific card lookup

        Args:
            card_id: The card ID to look up
            set_code: The set code to look up
            rarity: The rarity to look up
            page: The page number to look up
            pageSize: The page size to look up
        Returns:
            Complete URL for card endpoint
        """
        url = APIEndpointsConfig.CARDS_ENDPOINT
        
        # if card_id is provided it's a specific card lookup
        if card_id:
            url = f"{url}/{card_id}"
        else:
            # Build query parameters for filtering
            params = []
            if set_code:
                params.append(f"set={set_code}")
            if rarity:
                params.append(f"rarity={rarity}")
            if page is not None:
                params.append(f"page={page}")
            if pageSize is not None:
                params.append(f"pageSize={pageSize}")
            
            # Append query string if any params exist
            if params:
                url = f"{url}?{'&'.join(params)}"
        
        return url

    @staticmethod
    def get_set_url(set_code: Optional[str] = None) -> str:
        """
        Construct URL for specific set lookup

        Args:
            set_code: The set code to look up

        Returns:
            Complete URL for set endpoint
        """
        url = APIEndpointsConfig.SETS_ENDPOINT
        
        # if set_code is provided it's a specific set lookup
        if set_code:
            url = f"{url}/{set_code}"
        
        return url
