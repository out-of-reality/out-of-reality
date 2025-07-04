from odoo import Command

from odoo.addons.fastapi.tests.common import FastAPITransactionCase

from ..routers import levels


class TestLevelRoutes(FastAPITransactionCase):
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

        forward_pose = cls.env["pose.definition"].create({"name": "Forward Pose"})
        backward_pose = cls.env["pose.definition"].create({"name": "Backward Pose"})
        left_pose = cls.env["pose.definition"].create({"name": "Left Pose"})
        right_pose = cls.env["pose.definition"].create({"name": "Right Pose"})
        coin_pose = cls.env["pose.definition"].create({"name": "Coin Pose"})

        cls.env["level.configuration"].create(
            {
                "name": "Test Level 1",
                "level_number": 1,
                "active": True,
                "forward_pose_id": forward_pose.id,
                "backward_pose_id": backward_pose.id,
                "left_pose_id": left_pose.id,
                "right_pose_id": right_pose.id,
                "coin_challenge_time_limit": 10.0,
                "coin_pose_line_ids": [
                    Command.create({"sequence": 1, "pose_id": coin_pose.id})
                ],
            }
        )

    def test_get_first_level_success(self):
        with self._create_test_client(router=levels.router) as test_client:
            response = test_client.get("/levels/first_active")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["level_data"]["level_number"], 1)
        self.assertEqual(data["level_data"]["level_config_name"], "Test Level 1")
        self.assertIn("timestamp", data["level_data"])

    def test_get_level_configuration_success(self):
        with self._create_test_client(router=levels.router) as test_client:
            response = test_client.get("/levels/1")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["level_data"]["level_number"], 1)
        self.assertEqual(data["level_data"]["level_config_name"], "Test Level 1")
        self.assertEqual(data["level_data"]["patient_name"], "Test Partner")
        self.assertIn("timestamp", data["level_data"])

    def test_get_level_configuration_not_found(self):
        with self._create_test_client(router=levels.router) as test_client:
            response = test_client.get("/levels/999")

        self.assertEqual(response.status_code, 404)
