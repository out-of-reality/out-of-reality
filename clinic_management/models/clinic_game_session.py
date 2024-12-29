from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError


class ClinicGameSession(models.Model):
    _name = "clinic.game.session"
    _description = "Clinic Game Session"
    _rec_name = "patient_id"

    patient_id = fields.Many2one("res.partner", required=True)
    kinesiologist_ids = fields.Many2many("res.users")
    video = fields.Binary()
    filename = fields.Char()
    session_date = fields.Date(default=fields.Datetime.now)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            kinesiologists = (
                self.env["res.users.link"]
                .search(
                    [
                        ("patient_id", "=", vals["patient_id"]),
                        ("user_id.partner_type", "=", "kinesiologist"),
                    ]
                )
                .mapped("user_id")
            )
            if kinesiologists:
                vals["kinesiologist_ids"] = [Command.set(kinesiologists.ids)]
        return super().create(vals_list)

    @api.constrains("patient_id")
    def _check_patient(self):
        if self.filtered(lambda x: x.patient_id.partner_type != "patient"):
            raise ValidationError(_("Patients must be of type 'Patient'."))
