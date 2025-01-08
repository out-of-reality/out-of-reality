from odoo import _, api, fields, http, models
from odoo.exceptions import ValidationError


class ClinicGameSession(models.Model):
    _name = "clinic.game.session"
    _description = "Clinic Game Session"
    _rec_name = "patient_id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    patient_id = fields.Many2one(
        "res.partner", required=True, domain=[("partner_type", "=", "patient")]
    )
    video = fields.Binary()
    filename = fields.Char()
    session_date = fields.Date(default=fields.Datetime.now)

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

    def message_post(self, **kwargs):
        if (
            self._name == "clinic.game.session"
            and http.request
            and http.request.env.user.has_group("base.group_portal")
        ):
            self = self.sudo()
            self._subscribe_partners()
        return super().message_post(**kwargs)
