from odoo.tests.common import HttpCase


class TestGameSessionPortal(HttpCase):
    def setUp(self):
        super().setUp()
        group_portal = self.env.ref("base.group_portal")
        group_clinic_user = self.env.ref(
            "clinic_management.group_clinic_management_user"
        )

        self.portal_user = self.env["res.users"].create(
            {
                "name": "Portal User",
                "login": "portal_user",
                "email": "portal_user@example.com",
                "groups_id": [(4, group_portal.id)],
            }
        )
        self.portal_user.password = "portal_user"

        self.patient_user = self.env["res.users"].create(
            {
                "name": "Test Patient User",
                "login": "patient_user",
                "email": "patient_user@example.com",
                "partner_type": "patient",
                "self_managed": True,
                "groups_id": [(4, group_portal.id)],
            }
        )
        self.patient_user.password = "patient_user"
        self.patient = self.patient_user.partner_id

        self.kinesiologist_user = self.env["res.users"].create(
            {
                "name": "Test Kinesiologist User",
                "login": "kinesiologist_user",
                "email": "kinesiologist_user@example.com",
                "partner_type": "kinesiologist",
                "groups_id": [(4, group_clinic_user.id)],
            }
        )
        self.kinesiologist_user.password = "kinesiologist_user"
        self.kinesiologist = self.kinesiologist_user.partner_id

        self.link = self.env["res.users.link"].create(
            {
                "patient_id": self.patient.id,
                "user_id": self.kinesiologist_user.id,
            }
        )

        self.game_session = self.env["clinic.game.session"].create(
            {
                "patient_id": self.patient.id,
            }
        )

    def test_portal_access_game_sessions(self):
        self.authenticate("portal_user", "portal_user")
        response = self.url_open("/my/game_sessions")
        self.assertEqual(response.status_code, 200)

    def test_portal_access_individual_game_session(self):
        self.authenticate("portal_user", "portal_user")
        response = self.url_open(f"/my/game_sessions/{self.game_session.id}")
        self.assertEqual(response.status_code, 200)

    def test_game_session_sorting(self):
        self.authenticate("portal_user", "portal_user")
        response = self.url_open("/my/game_sessions?sortby=date")
        self.assertEqual(response.status_code, 200)

    def test_game_session_date_filter(self):
        self.authenticate("portal_user", "portal_user")
        response = self.url_open(
            "/my/game_sessions?date_begin=2023-01-01&date_end=2023-12-31"
        )
        self.assertEqual(response.status_code, 200)

    def test_patient_self_managed_access(self):
        self.authenticate("patient_user", "patient_user")
        response = self.url_open("/my/game_sessions")
        self.assertEqual(response.status_code, 200)

    def test_kinesiologist_access_linked_patients(self):
        self.authenticate("kinesiologist_user", "kinesiologist_user")
        response = self.url_open("/my/game_sessions")
        self.assertEqual(response.status_code, 200)

    def test_no_sessions_for_unlinked_kinesiologist(self):
        self.link.unlink()
        self.authenticate("kinesiologist_user", "kinesiologist_user")
        response = self.url_open("/my/game_sessions", timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.patient.name, response.text)
