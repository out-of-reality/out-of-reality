from odoo import fields, models


class HealthInsurance(models.Model):
    _name = "health.insurance"
    _description = "Health Insurance"

    name = fields.Char(required=True)
