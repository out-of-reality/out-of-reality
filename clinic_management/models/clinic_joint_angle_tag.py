from odoo import fields, models


class ClinicJointAngleTag(models.Model):
    _name = "clinic.joint.angle.tag"
    _description = "Joint Angle Tag for Selection"
    _order = "display_name_tag"
    _rec_name = "display_name_tag"

    name = fields.Char(
        string="Internal Name",
        required=True,
        index=True,
        help="Internal name or key for the joint angle, e.g., RIGHT_ELBOW."
        "Must match JointAngles Enum keys.",
    )
    display_name_tag = fields.Char(
        required=True,
        help="User-friendly name for the joint angle, e.g., Right Elbow.",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique (name)",
            "The internal name of the joint angle tag must be unique.",
        )
    ]
