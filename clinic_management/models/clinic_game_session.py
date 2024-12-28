from odoo import fields, models


class ClinicGameSession(models.Model):
    _name = "clinic.game.session"
    _description = "Clinic Game Session"
    _rec_name = "patient_id"

    patient_id = fields.Many2one("res.partner")
    video = fields.Binary()
    filename = fields.Char()
    session_date = fields.Date(default=fields.Datetime.now)
