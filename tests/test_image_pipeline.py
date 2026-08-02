"""Unit tests for the image pipeline's download-and-validate helper."""

import unittest
from unittest.mock import MagicMock

import requests

from database.etl.image_pipeline import fetch_card_image


def _mock_response(content=b"\xff\xd8\xff\xe0data", content_type="image/jpeg",
                   ok=True, status_code=200):
    """Build a fake requests.Response with the fields fetch_card_image reads."""
    resp = MagicMock()
    resp.ok = ok
    resp.status_code = status_code
    resp.headers = {"Content-Type": content_type}
    resp.content = content
    return resp


def _mock_session(response=None, side_effect=None):
    """Fake SessionManager whose .session.get returns/raises as configured."""
    session = MagicMock()
    if side_effect is not None:
        session.session.get.side_effect = side_effect
    else:
        session.session.get.return_value = response
    return session


NORMAL_URL = "https://cards.scryfall.io/normal/card.jpg"
PNG_URL = "https://cards.scryfall.io/png/card.png"


class TestFetchCardImage(unittest.TestCase):
    """Tests for fetch_card_image()."""

    def test_returns_image_from_normal_url(self):
        """Prefers the 'normal' size and returns its bytes + content type."""
        session = _mock_session(_mock_response())
        image_uris = {"small": "s", "normal": NORMAL_URL, "png": PNG_URL}

        result = fetch_card_image(session, image_uris)

        self.assertIsNotNone(result)
        self.assertEqual(result.content, b"\xff\xd8\xff\xe0data")
        self.assertEqual(result.content_type, "image/jpeg")
        self.assertEqual(result.source_url, NORMAL_URL)
        session.session.get.assert_called_once()
        self.assertEqual(session.session.get.call_args.args[0], NORMAL_URL)

    def test_falls_back_to_png_when_normal_absent(self):
        """Uses the 'png' url when 'normal' is missing."""
        session = _mock_session(_mock_response(content_type="image/png"))
        image_uris = {"small": "s", "png": PNG_URL}

        result = fetch_card_image(session, image_uris)

        self.assertIsNotNone(result)
        self.assertEqual(result.source_url, PNG_URL)
        self.assertEqual(result.content_type, "image/png")

    def test_returns_none_when_no_usable_size(self):
        """Skips the card (and makes no request) when neither size is present."""
        session = _mock_session(_mock_response())
        image_uris = {"small": "s", "large": "l"}

        result = fetch_card_image(session, image_uris)

        self.assertIsNone(result)
        session.session.get.assert_not_called()

    def test_returns_none_on_non_image_content_type(self):
        """Rejects an error page served with 200 (e.g. text/html)."""
        session = _mock_session(
            _mock_response(content=b"<html>404</html>", content_type="text/html")
        )
        image_uris = {"normal": NORMAL_URL}

        self.assertIsNone(fetch_card_image(session, image_uris))

    def test_returns_none_on_http_error_status(self):
        """Rejects a non-ok response even if it claims an image content type."""
        session = _mock_session(_mock_response(ok=False, status_code=404))
        image_uris = {"normal": NORMAL_URL}

        self.assertIsNone(fetch_card_image(session, image_uris))

    def test_returns_none_on_request_exception(self):
        """Swallows a network error and skips the card."""
        session = _mock_session(side_effect=requests.RequestException("boom"))
        image_uris = {"normal": NORMAL_URL}

        self.assertIsNone(fetch_card_image(session, image_uris))


if __name__ == "__main__":
    unittest.main()
