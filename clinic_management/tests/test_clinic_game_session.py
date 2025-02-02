from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import html2plaintext


class TestClinicGameSession(TransactionCase):
    def setUp(self):
        super().setUp()
        group_clinic_user = self.env.ref(
            "clinic_management.group_clinic_management_user"
        )
        group_portal = self.env.ref("base.group_portal")
        self.kinesiologist_user = self.env["res.users"].create(
            {
                "name": "Test Kinesiologist User",
                "login": "kinesiologist_user",
                "email": "kinesiologist@example.com",
                "partner_type": "kinesiologist",
                "groups_id": [(4, group_clinic_user.id)],
            }
        )
        self.kinesiologist = self.kinesiologist_user.partner_id

        self.guardian_user = self.env["res.users"].create(
            {
                "name": "Test Guardian User",
                "login": "guardian_user",
                "email": "guardian@example.com",
                "partner_type": "guardian",
                "groups_id": [(4, group_portal.id)],
            }
        )
        self.guardian = self.guardian_user.partner_id

        self.patient_user = self.env["res.users"].create(
            {
                "name": "Test Patient User",
                "login": "patient_user",
                "email": "patient@example.com",
                "partner_type": "patient",
                "self_managed": True,
                "groups_id": [(4, group_portal.id)],
            }
        )
        self.patient = self.patient_user.partner_id

        self.link = self.env["res.users.link"].create(
            {
                "patient_id": self.patient.id,
                "user_id": self.kinesiologist_user.id,
            }
        )

        self.game_session = self.env["clinic.game.session"].create(
            {
                "patient_id": self.patient.id,
                "state": "new",
            }
        )

    def test_compute_access_url(self):
        self.game_session._compute_access_url()
        self.assertIn("/my/game_sessions/", self.game_session.access_url)

    def test_check_patient(self):
        with self.assertRaises(ValidationError):
            self.game_session.patient_id = self.guardian

    def test_action_feedback_send(self):
        action = self.game_session.action_feedback_send()
        self.assertEqual(action["type"], "ir.actions.act_window")

    def test_message_post_as_portal_user(self):
        self.assertTrue(self.kinesiologist_user.email)
        self.game_session.with_user(self.kinesiologist_user).message_post(
            body="Test Message"
        )
        self.assertEqual(
            html2plaintext(self.game_session.message_ids[0].body), "Test Message"
        )

    def test_subscribe_partners(self):
        self.game_session._subscribe_partners()
        subscribed_partners = self.game_session.message_partner_ids
        self.assertIn(self.patient.id, subscribed_partners.ids)

    def test_find_mail_template(self):
        template = self.game_session._find_mail_template()
        self.assertIsNotNone(template)

    def test_action_preview_game_session(self):
        action = self.game_session.action_preview_game_session()
        self.assertEqual(action["type"], "ir.actions.act_url")

    def test_create_activity_on_create(self):
        new_session = self.env["clinic.game.session"].create(
            {
                "patient_id": self.patient.id,
            }
        )
        activity = self.env["mail.activity"].search(
            [("res_id", "=", new_session.id), ("res_model", "=", "clinic.game.session")]
        )
        self.assertTrue(activity)

    def test_check_mandatory_guardian_exception(self):
        with self.assertRaises(ValidationError):
            self.patient.self_managed = False

    def test_compute_wards_count(self):
        self.env["res.users.link"].create(
            {"user_id": self.guardian_user.id, "patient_id": self.patient.id}
        )
        self.guardian._compute_wards_count()
        self.assertEqual(self.guardian.wards_count, 1)

    def test_compute_patients_count(self):
        self.kinesiologist._compute_patients_count()
        self.assertEqual(self.kinesiologist.patients_count, 1)

    def test_open_related_wards(self):
        self.env["res.users.link"].create(
            {"user_id": self.guardian_user.id, "patient_id": self.patient.id}
        )
        action = self.guardian.open_related_wards()
        self.assertEqual(action["domain"], [("id", "in", [self.patient.id])])

    def test_open_related_patients(self):
        action = self.kinesiologist.open_related_patients()
        self.assertEqual(action["domain"], [("id", "in", [self.patient.id])])

    def test_get_partner_ids_for_notification(self):
        guardian1 = self.env["res.users"].create(
            {
                "name": "Guardian 1",
                "login": "guardian1",
                "email": "guardian1@example.com",
                "partner_type": "guardian",
            }
        )
        guardian2 = self.env["res.users"].create(
            {
                "name": "Guardian 2",
                "login": "guardian2",
                "email": "guardian2@example.com",
                "partner_type": "guardian",
            }
        )

        self.env["res.users.link"].create(
            {"user_id": guardian1.id, "patient_id": self.patient.id}
        )
        self.env["res.users.link"].create(
            {"user_id": guardian2.id, "patient_id": self.patient.id}
        )

        self.patient_user.self_managed = True
        partner_ids = self.game_session.get_partner_ids_for_notification()
        self.assertIn(self.patient.id, partner_ids)
        self.assertIn(guardian1.partner_id.id, partner_ids)
        self.assertIn(guardian2.partner_id.id, partner_ids)

        self.patient_user.self_managed = False
        partner_ids = self.game_session.get_partner_ids_for_notification()
        self.assertNotIn(self.patient.id, partner_ids)
        self.assertIn(guardian1.partner_id.id, partner_ids)
        self.assertIn(guardian2.partner_id.id, partner_ids)
