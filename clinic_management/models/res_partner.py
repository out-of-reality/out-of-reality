from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    partner_type = fields.Selection(
        [
            ("guardian", "Guardian"),
            ("patient", "Patient"),
            ("kinesiologist", "Kinesiologist"),
        ],
        compute="_compute_partner_type",
        readonly=False,
        store=True,
    )
    patient_link_ids = fields.One2many(
        "res.users.link", "patient_id", string="Contacts"
    )
    wards_count = fields.Integer(compute="_compute_wards_count")
    patients_count = fields.Integer(compute="_compute_patients_count")
    health_insurance_id = fields.Many2one("health.insurance")
    health_insurance_number = fields.Char()
    self_managed = fields.Boolean(
        help="""Indicates if the patient manages their
        own information without requiring a guardian."""
    )

    @api.depends("is_company")
    def _compute_partner_type(self):
        self.filtered(lambda x: x.is_company and x.partner_type).partner_type = False

    def _compute_wards_count(self):
        guardians = self.filtered(lambda x: x.partner_type == "guardian")
        for rec in guardians:
            rec.wards_count = self.env["res.users.link"].search_count(
                [("user_id.partner_id", "=", rec.id)]
            )
        (self - guardians).wards_count = 0

    def _compute_patients_count(self):
        kinesiologists = self.filtered(lambda x: x.partner_type == "kinesiologist")
        for rec in kinesiologists:
            rec.patients_count = self.env["res.users.link"].search_count(
                [("user_id.partner_id", "=", rec.id)]
            )
        (self - kinesiologists).patients_count = 0

    def open_related_wards(self):
        self.ensure_one()
        ward_ids = (
            self.env["res.users.link"]
            .search([("user_id.partner_id", "=", self.id)])
            .mapped("patient_id.id")
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", ward_ids)],
            "context": dict(self.env.context),
        }

    def open_related_patients(self):
        self.ensure_one()
        patient_ids = (
            self.env["res.users.link"]
            .search([("user_id.partner_id", "=", self.id)])
            .mapped("patient_id.id")
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", patient_ids)],
            "context": dict(self.env.context),
        }

    @api.constrains("patient_link_ids")
    def _check_mandatory_guardian(self):
        for rec in self.filtered(
            lambda x: x.partner_type == "patient" and not x.self_managed
        ):
            if not rec.patient_link_ids.filtered(
                lambda link: link.user_id.partner_id.partner_type == "guardian"
            ):
                raise ValidationError(
                    _(
                        "Each patient must have at least one linked contact with "
                        "partner type 'Guardian', unless marked as self-managed."
                    )
                )
