from unittest.mock import patch

from odoo import Command

from odoo.addons.fastapi.tests.common import FastAPITransactionCase

from ..routers import users


class TestUserRoutes(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_fastapi_running_user = cls.env.ref("base.user_admin")
        cls.default_fastapi_authenticated_partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "partner_type": "patient",
                "self_managed": True,
            }
        )
        cls.env["ir.config_parameter"].sudo().set_param("jwt.secret_key", "test_secret")

    def test_login_success(self):
        payload = {"username": "admin", "password": "admin"}

        with self._create_test_client(router=users.router) as test_client:
            response = test_client.post("/login", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        self.assertEqual(response.json()["name"], "Mitchell Admin")
        self.assertEqual(response.json()["email"], "admin@yourcompany.example.com")

    def test_login_non_self_managed_denied(self):
        group_portal = self.env.ref("base.group_portal")
        guardian = self.env["res.users"].create(
            {
                "name": "Guardian",
                "login": "guardian",
                "password": "guardian_password",
                "email": "guardian@example.com",
                "partner_type": "guardian",
                "groups_id": [Command.set([group_portal.id])],
            }
        )

        self.env["res.users"].create(
            {
                "name": "Non-Self Managed Patient User",
                "login": "non_self_managed_patient",
                "password": "test_password",
                "email": "non_self_managed@example.com",
                "partner_type": "patient",
                "self_managed": False,
                "groups_id": [Command.set([group_portal.id])],
                "patient_link_ids": [(0, 0, {"user_id": guardian.id})],
            }
        )

        payload = {"username": "non_self_managed_patient", "password": "test_password"}

        with self._create_test_client(router=users.router) as test_client:
            response = test_client.post("/login", json=payload)

        self.assertEqual(response.status_code, 401)

    @patch("odoo.addons.auth_faceid.utils.FaceIDService.identify_user")
    def test_faceid_login_success(self, mock_identify):
        group_portal = self.env.ref("base.group_portal")
        user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "email": "test@example.com",
                "partner_type": "patient",
                "self_managed": True,
                "groups_id": [Command.set([group_portal.id])],
            }
        )

        mock_identify.return_value = {"success": True, "user": user}

        payload = {"image": "base64_image_data"}

        with self._create_test_client(router=users.router) as test_client:
            response = test_client.post("/faceid_login", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
        self.assertEqual(response.json()["name"], "Test User")
        self.assertEqual(response.json()["email"], "test@example.com")

    @patch("odoo.addons.auth_faceid.utils.FaceIDService.identify_user")
    def test_faceid_login_failure(self, mock_identify):
        mock_identify.return_value = {
            "success": False,
            "message": "No matching face found",
        }

        payload = {"image": "base64_image_data"}

        with self._create_test_client(router=users.router) as test_client:
            response = test_client.post("/faceid_login", json=payload)

        self.assertEqual(response.status_code, 401)
        self.assertIn("No matching face found", response.json()["detail"])

    def test_whoami(self):
        with self._create_test_client(router=users.router) as test_client:
            response = test_client.get("/whoami")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Partner")
