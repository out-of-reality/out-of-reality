from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..utils.video_processor import JointAngles


class PoseAngleRequirement(models.Model):
    _name = "pose.angle.requirement"
    _description = "Pose Angle Requirement"
    _order = "angle_type"

    pose_id = fields.Many2one(
        "pose.definition", string="Pose", required=True, ondelete="cascade"
    )
    angle_type = fields.Selection(selection="_get_angle_type_selection", required=True)
    min_angle = fields.Float(
        string="Minimum Angle (°)",
        required=True,
        digits=(5, 2),
        help="Minimum angle in degrees to consider this requirement valid",
    )
    max_angle = fields.Float(
        string="Maximum Angle (°)",
        required=True,
        digits=(5, 2),
        help="Maximum angle in degrees to consider this requirement valid",
    )
    description = fields.Text(string="Requirement Description")

    angle_range = fields.Float(
        string="Angle Range (°)",
        compute="_compute_angle_metrics",
        store=True,
        digits=(5, 2),
        help="Difference between maximum and minimum angle",
    )
    angle_midpoint = fields.Float(
        string="Midpoint (°)",
        compute="_compute_angle_metrics",
        store=True,
        digits=(5, 2),
        help="Midpoint of the angle range",
    )

    @api.model
    def _get_angle_type_selection(self):
        return [
            (angle.name, angle.name.replace("_", " ").title()) for angle in JointAngles
        ]

    @api.depends("min_angle", "max_angle")
    def _compute_angle_metrics(self):
        for record in self:
            if record.max_angle is not None and record.min_angle is not None:
                record.angle_range = record.max_angle - record.min_angle
                record.angle_midpoint = (record.min_angle + record.max_angle) / 2
            else:
                record.angle_range = 0
                record.angle_midpoint = 0

    @api.constrains("pose_id", "angle_type")
    def _validate_unique_angle_per_pose(self):
        for record in self:
            if not record.pose_id or not record.angle_type:
                continue

            domain = [
                ("pose_id", "=", record.pose_id.id),
                ("angle_type", "=", record.angle_type),
                ("id", "!=", record.id),
            ]

            existing = self.search(domain, limit=1)
            if existing:
                angle_label = record.angle_type
                selection_dict = dict(self._get_angle_type_selection())
                angle_label = selection_dict.get(record.angle_type, record.angle_type)
                raise ValidationError(
                    _(
                        "Angle '%(angle_type)s' is already defined "
                        "for pose '%(pose_name)s'."
                    )
                    % {"angle_type": angle_label, "pose_name": record.pose_id.name}
                )

    @api.constrains("min_angle", "max_angle")
    def _check_angles(self):
        for record in self:
            if record.min_angle is not None and record.min_angle < 0:
                raise ValidationError(
                    _(
                        "Angle %(angle_type)s: "
                        "minimum (%(min_angle)s°) cannot be negative."
                    )
                    % {"angle_type": record.angle_type, "min_angle": record.min_angle}
                )

            if record.max_angle is not None and record.max_angle > 180:
                raise ValidationError(
                    _("Angle %(angle_type)s: maximum (%(max_angle)s°) exceeds 180°.")
                    % {"angle_type": record.angle_type, "max_angle": record.max_angle}
                )

            if (
                record.min_angle is not None
                and record.max_angle is not None
                and record.min_angle >= record.max_angle
            ):
                raise ValidationError(
                    _(
                        "Angle %(angle_type)s: minimum (%(min_angle)s°) "
                        "must be less than maximum (%(max_angle)s°)."
                    )
                    % {
                        "angle_type": record.angle_type,
                        "min_angle": record.min_angle,
                        "max_angle": record.max_angle,
                    }
                )

    @api.onchange("min_angle", "max_angle")
    def _onchange_validate_angles(self):
        if not self.min_angle or not self.max_angle:
            return

        warnings = []
        if self.min_angle < 0:
            warnings.append("⚠️ Minimum angle cannot be negative.")

        if self.max_angle > 180:
            warnings.append("⚠️ Maximum angle exceeds 180°.")

        if self.min_angle >= self.max_angle:
            warnings.append("⚠️ Minimum angle must be less than maximum.")

        if self.min_angle < self.max_angle:
            angle_range = self.max_angle - self.min_angle
            if angle_range > 90:
                warnings.append(
                    "⚠️ Very wide range (%.1f°), may be too permissive." % angle_range
                )
            elif angle_range < 10:
                warnings.append(
                    "⚠️ Very narrow range (%.1f°), may be difficult to detect."
                    % angle_range
                )

        if warnings:
            return {
                "warning": {
                    "title": _("Configuration Warning"),
                    "message": "\n".join(warnings),
                }
            }

    @api.onchange("angle_type", "pose_id")
    def _onchange_check_duplicate_angle(self):
        if not self.pose_id or not self.angle_type:
            return

        domain = [
            ("pose_id", "=", self.pose_id.id),
            ("angle_type", "=", self.angle_type),
        ]

        if self.id:
            domain.append(("id", "!=", self.id))

        existing = self.search(domain, limit=1)
        if existing:
            selection_dict = dict(self._get_angle_type_selection())
            angle_label = selection_dict.get(self.angle_type, self.angle_type)

            return {
                "warning": {
                    "title": _("Duplicate Angle"),
                    "message": _(
                        "Angle '%(angle_type)s' is already defined for this pose."
                    )
                    % {"angle_type": angle_label},
                }
            }
