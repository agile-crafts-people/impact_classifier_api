"""
Unit tests for sentiment routes.

These tests validate the Flask route layer for the sentiment domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.sentiment_routes import create_sentiment_routes


class TestsentimentRoutes(unittest.TestCase):
    """Test cases for sentiment routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_sentiment_routes(),
            url_prefix="/api/sentiment",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.sentiment_routes.create_flask_token")
    @patch("src.routes.sentiment_routes.create_flask_breadcrumb")
    @patch("src.routes.sentiment_routes.sentimentService.create_sentiment")
    @patch("src.routes.sentiment_routes.sentimentService.get_sentiment")
    def test_create_sentiment_success(
        self,
        mock_get_sentiment,
        mock_create_sentiment,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/sentiment for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_sentiment.return_value = "123"
        mock_get_sentiment.return_value = {
            "_id": "123",
            "name": "test-sentiment",
            "status": "active",
        }

        response = self.client.post(
            "/api/sentiment",
            json={"name": "test-sentiment", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_sentiment.assert_called_once()
        mock_get_sentiment.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.sentiment_routes.create_flask_token")
    @patch("src.routes.sentiment_routes.create_flask_breadcrumb")
    @patch("src.routes.sentiment_routes.sentimentService.get_sentiments")
    def test_get_sentiments_no_filter(
        self,
        mock_get_sentiments,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/sentiment without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_sentiments.return_value = {
            "items": [
                {"_id": "123", "name": "sentiment1"},
                {"_id": "456", "name": "sentiment2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/sentiment")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_sentiments.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.sentiment_routes.create_flask_token")
    @patch("src.routes.sentiment_routes.create_flask_breadcrumb")
    @patch("src.routes.sentiment_routes.sentimentService.get_sentiments")
    def test_get_sentiments_with_name_filter(
        self,
        mock_get_sentiments,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/sentiment with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_sentiments.return_value = {
            "items": [{"_id": "123", "name": "test-sentiment"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/sentiment?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_sentiments.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.sentiment_routes.create_flask_token")
    @patch("src.routes.sentiment_routes.create_flask_breadcrumb")
    @patch("src.routes.sentiment_routes.sentimentService.get_sentiment")
    def test_get_sentiment_success(
        self,
        mock_get_sentiment,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/sentiment/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_sentiment.return_value = {
            "_id": "123",
            "name": "sentiment1",
        }

        response = self.client.get("/api/sentiment/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_sentiment.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.sentiment_routes.create_flask_token")
    @patch("src.routes.sentiment_routes.create_flask_breadcrumb")
    @patch("src.routes.sentiment_routes.sentimentService.get_sentiment")
    def test_get_sentiment_not_found(
        self,
        mock_get_sentiment,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/sentiment/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_sentiment.side_effect = HTTPNotFound(
            "sentiment 999 not found"
        )

        response = self.client.get("/api/sentiment/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "sentiment 999 not found")

    @patch("src.routes.sentiment_routes.create_flask_token")
    def test_create_sentiment_unauthorized(self, mock_create_token):
        """Test POST /api/sentiment when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/sentiment",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
