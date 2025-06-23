import json
from base64 import b64encode
from io import BytesIO
from unittest.mock import Mock, patch

from PIL import Image

from odoo.tests.common import HttpCase


class TestAuthFaceID(HttpCase):
    def setUp(self):
        super().setUp()
        self.user = self.env["res.users"].search([("login", "=", "demo")], limit=1)
        self.user.face_encoding = b"fake_encoding_data"

    def _generate_test_image(self):
        """Generate a simple white test image"""
        image = Image.new("RGB", (128, 128), color=(255, 255, 255))
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        return b64encode(buffered.getvalue()).decode()

    @patch("requests.post")
    def test_verify_face_success(self, mock_post):
        """Test successful face verification"""
        # Mock the face encoding request
        mock_encoding_response = Mock()
        mock_encoding_response.status_code = 200
        mock_encoding_response.json.return_value = {"encoding": [0.1, 0.2, 0.3]}

        # Mock the face comparison request
        mock_compare_response = Mock()
        mock_compare_response.status_code = 200
        mock_compare_response.json.return_value = {"matched_index": 0}

        mock_post.side_effect = [mock_encoding_response, mock_compare_response]

        image_data = self._generate_test_image()
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"image": f"data:image/jpeg;base64,{image_data}"},
        }
        response = self.url_open(
            "/web/login/verify_face",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json().get("result", {})
        self.assertIn("success", result)
        self.assertTrue(result["success"])

    @patch("requests.post")
    def test_verify_face_no_face_detected(self, mock_post):
        """Test when no face is detected"""
        # Mock the face encoding request to fail
        mock_encoding_response = Mock()
        mock_encoding_response.status_code = 400
        mock_post.return_value = mock_encoding_response

        blank_image_data = self._generate_test_image()
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"image": f"data:image/jpeg;base64,{blank_image_data}"},
        }
        response = self.url_open(
            "/web/login/verify_face",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json().get("result", {})
        self.assertIn("success", result)
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "No face detected.")

    @patch("requests.post")
    def test_verify_face_no_user_with_encoding(self, mock_post):
        """Test when no users have face encodings"""
        # Remove face encoding from all users
        all_users = self.env["res.users"].sudo().search([])
        all_users.write({"face_encoding": False})

        # Mock successful face encoding
        mock_encoding_response = Mock()
        mock_encoding_response.status_code = 200
        mock_encoding_response.json.return_value = {"encoding": [0.1, 0.2, 0.3]}
        mock_post.return_value = mock_encoding_response

        image_data = self._generate_test_image()
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {"image": f"data:image/jpeg;base64,{image_data}"},
        }
        response = self.url_open(
            "/web/login/verify_face",
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        result = response.json().get("result", {})
        self.assertIn("success", result)
        self.assertFalse(result["success"])
        self.assertEqual(result["message"], "No users with face encodings.")
