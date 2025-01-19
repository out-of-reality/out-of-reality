import json
import os
from base64 import b64encode
from io import BytesIO

from PIL import Image

from odoo.tests.common import HttpCase


class TestAuthFaceID(HttpCase):
    def setUp(self):
        super().setUp()
        self.user = self.env["res.users"].search([("login", "=", "demo")], limit=1)
        self.user.image_512 = self._load_test_face_image()

    def _load_test_face_image(self):
        image_path = os.path.join(
            os.path.dirname(__file__), "../static/src/img/face.jpg"
        )
        with open(image_path, "rb") as image_file:
            return b64encode(image_file.read()).decode()

    def _generate_blank_image(self):
        image = Image.new("RGB", (128, 128), color=(255, 255, 255))
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        return b64encode(buffered.getvalue()).decode()

    def test_verify_face_success(self):
        image_data = self._load_test_face_image()
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

    def test_verify_face_no_face_detected(self):
        blank_image_data = self._generate_blank_image()
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
        self.assertEqual(result["message"], "No face detected in the captured image.")

    def test_verify_face_no_user_with_encoding(self):
        self.user.face_encoding = False
        image_data = self._load_test_face_image()
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
        self.assertEqual(
            result["message"], "No users with registered face encodings found."
        )
