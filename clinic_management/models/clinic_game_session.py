from odoo import _, api, fields, http, models
from odoo.exceptions import ValidationError


class ClinicGameSession(models.Model):
    _name = "clinic.game.session"
    _description = "Clinic Game Session"
    _rec_name = "patient_id"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]

    patient_id = fields.Many2one(
        "res.partner", required=True, domain=[("partner_type", "=", "patient")]
    )
    video = fields.Binary()
    filename = fields.Char()
    session_date = fields.Date(default=fields.Datetime.now)
    state = fields.Selection(
        [("new", "New"), ("done", "Done")], default="new", tracking=True
    )
    feedback = fields.Html()

    def _message_get_suggested_recipients(self):
        res = super()._message_get_suggested_recipients()
        for partner in self.patient_id.patient_link_ids.mapped("user_id.partner_id"):
            self._message_add_suggested_recipient(res, partner=partner)
        return res

    def _subscribe_partners(self):
        for record in self:
            partners_to_subscribe = record.patient_id.patient_link_ids.mapped(
                "user_id.partner_id.id"
            )
            if partners_to_subscribe:
                record.message_subscribe(partner_ids=partners_to_subscribe)

    @api.constrains("patient_id")
    def _check_patient(self):
        if self.filtered(lambda x: x.patient_id.partner_type != "patient"):
            raise ValidationError(_("Patients must be of type 'Patient'."))

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get("mark_gs_as_sent"):
            self.filtered(lambda x: x.state == "new").write({"state": "done"})
        if (
            self._name == "clinic.game.session"
            and http.request
            and http.request.env.user.has_group("base.group_portal")
        ):
            self = self.sudo()
            self._subscribe_partners()
        return super().message_post(**kwargs)

    @api.model_create_multi
    def create(self, vals_list):
        record = super().create(vals_list)

        kinesiologists = record.patient_id.patient_link_ids.filtered(
            lambda link: link.user_id.partner_id.partner_type == "kinesiologist"
        ).mapped("user_id")

        for kinesiologist in kinesiologists:
            record.activity_schedule(
                activity_type_id=self.env.ref("mail.mail_activity_data_todo").id,
                user_id=kinesiologist.id,
                summary=_("Review game session for %s") % record.patient_id.name,
                date_deadline=fields.Date.today(),
            )

        return record

    def _find_mail_template(self):
        self.ensure_one()
        return self.env.ref(
            "clinic_management.email_template_clinic_session", raise_if_not_found=False
        )

    def action_feedback_send(self):
        self.ensure_one()
        mail_template = self._find_mail_template()
        ctx = {
            "default_model": "clinic.game.session",
            "default_res_ids": self.ids,
            "default_template_id": mail_template.id if mail_template else None,
            "default_composition_mode": "comment",
            "mark_gs_as_sent": True,
            "default_email_layout_xmlid": (
                "mail.mail_notification_layout_with_responsible_signature"
            ),
            "force_email": True,
            "user_name": self.env.user.name,
        }
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": ctx,
        }

    def action_preview_game_session(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "new",
            "url": self.get_portal_url(),
        }

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for rec in self:
            rec.access_url = f"/my/game_sessions/{rec.id}"
        return res
