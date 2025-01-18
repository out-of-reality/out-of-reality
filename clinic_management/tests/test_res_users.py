from odoo import Command
from odoo.exceptions import AccessDenied
from odoo.tests.common import HttpCase


class TestResUsersLogin(HttpCase):
    def setUp(self):
        super().setUp()
        group_portal = self.env.ref("base.group_portal")

        self.guardian = self.env["res.users"].create(
            {
                "name": "Guardian 1",
                "login": "guardian1",
                "password": "guardian_password",
                "email": "guardian1@example.com",
                "partner_type": "guardian",
                "groups_id": [Command.set([group_portal.id])],
            }
        )

        self.patient_user = self.env["res.users"].create(
            {
                "name": "Non-Self Managed Patient User",
                "login": "non_self_managed_patient",
                "password": "non_self_managed_password",
                "email": "non_self_managed@example.com",
                "partner_type": "patient",
                "self_managed": False,
                "groups_id": [Command.set([group_portal.id])],
                "patient_link_ids": [(0, 0, {"user_id": self.guardian.id})],
            }
        )

        self.self_managed_patient_user = self.env["res.users"].create(
            {
                "name": "Self Managed Patient User",
                "login": "self_managed_patient",
                "password": "self_managed_password",
                "email": "self_managed@example.com",
                "partner_type": "patient",
                "self_managed": True,
                "groups_id": [Command.set([group_portal.id])],
            }
        )

    def test_access_denied_for_non_self_managed_patient(self):
        with self.assertRaises(AccessDenied):
            self.authenticate("non_self_managed_patient", "non_self_managed_password")

    def test_successful_login_for_self_managed_patient(self):
        self.authenticate("self_managed_patient", "self_managed_password")
        response = self.url_open("/my/home")
        self.assertEqual(response.status_code, 200)
