"""
Request manager for handling API requests.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.config.api_endpoints import APIEndpointsConfig

DEFAULT_TIMEOUT = 30  # sec
MAX_RETRIES = 3


class SessionManager:
    """
    Manages HTTP requests with retry logic and rate limiting.

    This class provides a configured requests.Session for making API calls
    with built-in retry logic.
    """

    def __init__(self, timeout: int = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        """Create a requests Session with retry strategy and default headers."""
        session = requests.Session()
        session.headers.update(APIEndpointsConfig.DEFAULT_HEADERS)
        retry = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session