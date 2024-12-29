from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsersLink(models.Model):
    _name = "res.users.link"
    _description = "Res Users Link"
    _order = "relationship"

    patient_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", required=True, ondelete="restrict")
    relationship = fields.Selection(related="user_id.partner_type", store=True)
    note = fields.Text()

    _sql_constraints = [
        (
            "link_unique",
            "unique(patient_id, user_id)",
            _("The contact must be added on a one-time basis with the patient."),
        )
    ]

    @api.constrains("patient_id")
    def _check_patient_type(self):
        if self.filtered(
            lambda x: x.patient_id and x.patient_id.partner_type != "patient"
        ):
            raise ValidationError(
                _("The Patients must have the partner type 'Patient'.")
            )
