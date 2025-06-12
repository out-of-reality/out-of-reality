from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PoseDefinition(models.Model):
    _name = "pose.definition"
    _description = "Custom Pose Definition"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Pose Name", required=True)
    description = fields.Text()

    angle_requirements_ids = fields.One2many(
        "pose.angle.requirement", "pose_id", string="Angle Requirements"
    )

    require_feet_on_ground = fields.Boolean(
        string="Require Feet on Ground",
        default=True,
        help="If checked, the pose will only be detected if feet are on the ground",
    )
    foot_tolerance_y = fields.Float(
        string="Y Tolerance for Feet",
        default=0.08,
        help="Tolerance to verify if " 'foot points are "close" in Y (flat foot)',
    )

    @api.constrains("angle_requirements_ids")
    def _check_angle_requirements(self):
        for record in self:
            if not record.angle_requirements_ids:
                raise ValidationError(
                    _("A pose must have at least one angle requirement defined.")
                )

    @api.constrains("foot_tolerance_y")
    def _check_foot_tolerance(self):
        for record in self:
            if not (0 <= record.foot_tolerance_y <= 1):
                raise ValidationError(_("Foot tolerance must be between 0 and 1."))

    @api.constrains("require_feet_on_ground", "foot_tolerance_y")
    def _check_foot_tolerance_range(self):
        for record in self:
            if record.require_feet_on_ground and not (
                0.01 <= record.foot_tolerance_y <= 0.5
            ):
                return {
                    "warning": {
                        "title": _("Configuration Warning"),
                        "message": _(
                            "Foot tolerance (%.3f) "
                            "outside recommended range (0.01-0.5)."
                        )
                        % record.foot_tolerance_y,
                    }
                }

    def get_pose_data_for_unity(self):
        self.ensure_one()
        angle_requirements = [
            {
                "angle": req.angle_type,
                "min_angle": req.min_angle,
                "max_angle": req.max_angle,
                "description": req.description or "",
            }
            for req in self.angle_requirements_ids
        ]

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "angle_requirements": angle_requirements,
            "require_feet_on_ground": self.require_feet_on_ground,
            "foot_tolerance_y": self.foot_tolerance_y,
        }
