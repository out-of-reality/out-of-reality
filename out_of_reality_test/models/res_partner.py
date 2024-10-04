from odoo import fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    video = fields.Binary()
    filename = fields.Char()
