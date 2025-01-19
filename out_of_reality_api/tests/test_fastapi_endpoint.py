from odoo.addons.fastapi.tests.common import FastAPITransactionCase


class TestOutOfRealityAPI(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.endpoint = cls.env["fastapi.endpoint"].search(
            [("app", "=", "out_of_reality")], limit=1
        )
        cls.endpoint.action_sync_registry()
        cls.test_user = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "password": "secure_password",
                "email": "test_user@example.com",
            }
        )

    def test_login_success(self):
        with self._create_test_client(app=self.endpoint._get_app()) as client:
            payload = {
                "username": "demo",
                "password": "demo",
            }
            response = client.post("/login", json=payload)

            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertIn("access_token", result)
            self.assertEqual(result["id"], self.env.ref("base.user_demo").id)
