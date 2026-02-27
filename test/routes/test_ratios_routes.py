"""
Unit tests for ratios routes.

These tests validate the Flask route layer for the ratios domain, using the
generated blueprint factory and mocking out the underlying service and
token/breadcrumb helpers from api_utils.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from src.routes.ratios_routes import create_ratios_routes


class TestratiosRoutes(unittest.TestCase):
    """Test cases for ratios routes."""

    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(
            create_ratios_routes(),
            url_prefix="/api/ratios",
        )
        self.client = self.app.test_client()

        self.mock_token = {"user_id": "test_user", "roles": ["admin"]}
        self.mock_breadcrumb = {"at_time": "sometime", "correlation_id": "correlation_ID"}

    @patch("src.routes.ratios_routes.create_flask_token")
    @patch("src.routes.ratios_routes.create_flask_breadcrumb")
    @patch("src.routes.ratios_routes.ratiosService.create_ratios")
    @patch("src.routes.ratios_routes.ratiosService.get_ratios")
    def test_create_ratios_success(
        self,
        mock_get_ratios,
        mock_create_ratios,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test POST /api/ratios for successful creation."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_create_ratios.return_value = "123"
        mock_get_ratios.return_value = {
            "_id": "123",
            "name": "test-ratios",
            "status": "active",
        }

        response = self.client.post(
            "/api/ratios",
            json={"name": "test-ratios", "status": "active"},
        )

        self.assertEqual(response.status_code, 201)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_create_ratios.assert_called_once()
        mock_get_ratios.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.ratios_routes.create_flask_token")
    @patch("src.routes.ratios_routes.create_flask_breadcrumb")
    @patch("src.routes.ratios_routes.ratiosService.get_ratioss")
    def test_get_ratioss_no_filter(
        self,
        mock_get_ratioss,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/ratios without name filter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_ratioss.return_value = {
            "items": [
                {"_id": "123", "name": "ratios1"},
                {"_id": "456", "name": "ratios2"},
            ],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/ratios")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 2)
        mock_get_ratioss.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name=None,
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.ratios_routes.create_flask_token")
    @patch("src.routes.ratios_routes.create_flask_breadcrumb")
    @patch("src.routes.ratios_routes.ratiosService.get_ratioss")
    def test_get_ratioss_with_name_filter(
        self,
        mock_get_ratioss,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/ratios with name query parameter."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_ratioss.return_value = {
            "items": [{"_id": "123", "name": "test-ratios"}],
            "limit": 10,
            "has_more": False,
            "next_cursor": None,
        }

        response = self.client.get("/api/ratios?name=test")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIsInstance(data, dict)
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 1)
        mock_get_ratioss.assert_called_once_with(
            self.mock_token,
            self.mock_breadcrumb,
            name="test",
            after_id=None,
            limit=10,
            sort_by="name",
            order="asc",
        )

    @patch("src.routes.ratios_routes.create_flask_token")
    @patch("src.routes.ratios_routes.create_flask_breadcrumb")
    @patch("src.routes.ratios_routes.ratiosService.get_ratios")
    def test_get_ratios_success(
        self,
        mock_get_ratios,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/ratios/<id> for successful response."""
        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_ratios.return_value = {
            "_id": "123",
            "name": "ratios1",
        }

        response = self.client.get("/api/ratios/123")

        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data["_id"], "123")
        mock_get_ratios.assert_called_once_with(
            "123", self.mock_token, self.mock_breadcrumb
        )

    @patch("src.routes.ratios_routes.create_flask_token")
    @patch("src.routes.ratios_routes.create_flask_breadcrumb")
    @patch("src.routes.ratios_routes.ratiosService.get_ratios")
    def test_get_ratios_not_found(
        self,
        mock_get_ratios,
        mock_create_breadcrumb,
        mock_create_token,
    ):
        """Test GET /api/ratios/<id> when document is not found."""
        from api_utils.flask_utils.exceptions import HTTPNotFound

        mock_create_token.return_value = self.mock_token
        mock_create_breadcrumb.return_value = self.mock_breadcrumb

        mock_get_ratios.side_effect = HTTPNotFound(
            "ratios 999 not found"
        )

        response = self.client.get("/api/ratios/999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json["error"], "ratios 999 not found")

    @patch("src.routes.ratios_routes.create_flask_token")
    def test_create_ratios_unauthorized(self, mock_create_token):
        """Test POST /api/ratios when token is invalid."""
        from api_utils.flask_utils.exceptions import HTTPUnauthorized

        mock_create_token.side_effect = HTTPUnauthorized("Invalid token")

        response = self.client.post(
            "/api/ratios",
            json={"name": "test"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)


if __name__ == "__main__":
    unittest.main()
