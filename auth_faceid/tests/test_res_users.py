import os
from base64 import b64encode

from odoo.tests.common import TransactionCase


class TestResUsers(TransactionCase):
    def test_face_encoding_computation(self):
        user = self.env["res.users"].search([("login", "=", "demo")], limit=1)
        user.image_512 = self._load_test_face_image()
        self.assertTrue(user.face_encoding)

    def test_face_encoding_no_image(self):
        user = self.env["res.users"].search([("login", "=", "demo")], limit=1)
        self.assertFalse(user.face_encoding)

    def _load_test_face_image(self):
        image_path = os.path.join(
            os.path.dirname(__file__), "../static/src/img/face.jpg"
        )
        with open(image_path, "rb") as image_file:
            return b64encode(image_file.read()).decode()
