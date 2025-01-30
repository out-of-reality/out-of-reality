import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class LevelConfiguration(models.Model):
    _name = "level.configuration"
    _description = "Game Level Configuration"
    _rec_name = "name"
    _order = "level_number, name"

    name = fields.Char(
        required=True,
        copy=False,
        help="A descriptive name for this level configuration "
        "(e.g., 'Standard Level 1', 'Advanced Level 1 - Therapy Group A').",
    )
    level_number = fields.Integer(
        required=True,
        index=True,
        help="Level identifier (1, 2, 3, etc.)",
    )
    partner_ids = fields.Many2many(
        "res.partner",
        "level_configuration_res_partner_rel",
        "level_config_id",
        "partner_id",
        string="Patients",
        domain=[("partner_type", "=", "patient")],
        help="Patients this configuration applies to. "
        "A patient can only have one active configuration per level number.",
    )
    description = fields.Text(string="Configuration Description")
    active = fields.Boolean(default=True, index=True)

    forward_pose_id = fields.Many2one(
        "pose.definition",
        string="Forward Movement Pose",
        domain=[("active", "=", True)],
        ondelete="cascade",
        help="Pose required for forward movement",
    )
    backward_pose_id = fields.Many2one(
        "pose.definition",
        string="Backward Movement Pose",
        domain=[("active", "=", True)],
        ondelete="cascade",
        help="Pose required for backward movement",
    )
    left_pose_id = fields.Many2one(
        "pose.definition",
        string="Left Movement Pose",
        domain=[("active", "=", True)],
        ondelete="cascade",
        help="Pose required for left movement",
    )
    right_pose_id = fields.Many2one(
        "pose.definition",
        string="Right Movement Pose",
        domain=[("active", "=", True)],
        ondelete="cascade",
        help="Pose required for right movement",
    )

    coin_pose_line_ids = fields.One2many(
        "level.coin.pose.line",
        "level_config_id",
        string="Coin Poses Sequence",
        help="Ordered sequence of poses for coin challenges. Poses can repeat.",
    )

    coin_challenge_time_limit = fields.Float(
        string="Coin Challenge Time Limit (seconds)",
        required=True,
        default=10.0,
        digits=(5, 2),
        help="Time limit in seconds for coin pose challenges",
    )

    _sql_constraints = [
        (
            "name_level_uniq",
            "unique(name, level_number)",
            "A configuration with this name and level number already exists!",
        )
    ]

    @api.constrains("level_number", "partner_ids", "active")
    def _check_unique_active_level_per_patient(self):
        for record in self:
            if not record.active or not record.partner_ids:
                continue
            for patient in record.partner_ids:
                domain = [
                    ("level_number", "=", record.level_number),
                    ("partner_ids", "in", [patient.id]),
                    ("id", "!=", record.id),
                    ("active", "=", True),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        _(
                            "Patient %(patient_name)s already has "
                            "an active configuration for level %(level_number)s."
                        )
                        % {
                            "patient_name": patient.name,
                            "level_number": record.level_number,
                        }
                    )

    @api.constrains("coin_challenge_time_limit")
    def _check_time_limit(self):
        for record in self:
            if not (1.0 <= record.coin_challenge_time_limit <= 60.0):
                raise ValidationError(
                    _("Coin challenge time limit must be between 1 and 60 seconds.")
                )

    @api.constrains(
        "level_number",
        "forward_pose_id",
        "backward_pose_id",
        "left_pose_id",
        "right_pose_id",
        "coin_pose_line_ids",
    )  # Updated field name
    def _validate_level_configuration(self):
        for record in self:
            if record.level_number == 1:
                missing_movement_poses = []
                if not record.forward_pose_id:
                    missing_movement_poses.append("Forward Movement Pose")
                if not record.backward_pose_id:
                    missing_movement_poses.append("Backward Movement Pose")
                if not record.left_pose_id:
                    missing_movement_poses.append("Left Movement Pose")
                if not record.right_pose_id:
                    missing_movement_poses.append("Right Movement Pose")

                if missing_movement_poses:
                    raise ValidationError(
                        _(
                            "Level 1 ('%(config_name)s') "
                            "requires all movement poses."
                            "Missing: %(missing_poses)s"
                        )
                        % {
                            "config_name": record.name,
                            "missing_poses": ", ".join(missing_movement_poses),
                        }
                    )
                # Check the count of coin_pose_line_ids
                if len(record.coin_pose_line_ids) != 3:
                    raise ValidationError(
                        _(
                            "Level 1 ('%(config_name)s') "
                            "requires exactly 3 coin poses. "
                            "Currently has: %(current_count)s"
                        )
                        % {
                            "config_name": record.name,
                            "current_count": len(record.coin_pose_line_ids),
                        }
                    )

    def get_level_data_for_unity(self, partner_id_value, partner_name_value):
        """Returns level configuration data
        in JSON format for Unity with patient context."""
        self.ensure_one()

        def get_pose_data(pose_record):
            if pose_record:
                return pose_record.get_pose_data_for_unity()
            return None

        coin_poses_data = {
            f"coin{idx + 1}": get_pose_data(
                pose_line.pose_id
            )  # Access pose_id from the line record
            for idx, pose_line in enumerate(
                self.coin_pose_line_ids.sorted("sequence")
            )  # Ensure correct order
        }

        return {
            "level_config_name": self.name,
            "level_number": self.level_number,
            "patient_id": partner_id_value,
            "patient_name": partner_name_value,
            "movement_poses": {
                "forward": get_pose_data(self.forward_pose_id),
                "backward": get_pose_data(self.backward_pose_id),
                "left": get_pose_data(self.left_pose_id),
                "right": get_pose_data(self.right_pose_id),
            },
            "coin_poses": coin_poses_data,
            "timing": {"coin_challenge_time_limit": self.coin_challenge_time_limit},
            "timestamp": fields.Datetime.now().isoformat(),
        }

    def get_data_for_unity(self):
        """Returns level configuration data
        in JSON format for Unity without patient context."""
        self.ensure_one()

        def get_pose_data(pose_record):
            if pose_record:
                return pose_record.get_pose_data_for_unity()
            return None

        coin_poses_data = {
            f"coin{idx + 1}": get_pose_data(
                pose_line.pose_id
            )  # Access pose_id from the line record
            for idx, pose_line in enumerate(
                self.coin_pose_line_ids.sorted("sequence")
            )  # Ensure correct order
        }
        return {
            "level_config_name": self.name,
            "level_number": self.level_number,
            "movement_poses": {
                "forward": get_pose_data(self.forward_pose_id),
                "backward": get_pose_data(self.backward_pose_id),
                "left": get_pose_data(self.left_pose_id),
                "right": get_pose_data(self.right_pose_id),
            },
            "coin_poses": coin_poses_data,
            "timing": {"coin_challenge_time_limit": self.coin_challenge_time_limit},
            "timestamp": fields.Datetime.now().isoformat(),
        }

    @api.model
    def get_level_configuration_for_patient(self, level_number, partner_id):
        """Get active level configuration for a specific patient and level number."""
        if not isinstance(partner_id, int):
            raise ValidationError(_("Patient ID must be an integer."))

        patient = self.env["res.partner"].browse(partner_id)
        if not patient.exists():
            raise ValidationError(_("Patient with ID %s not found.") % partner_id)

        domain_patient_specific = [
            ("level_number", "=", level_number),
            ("partner_ids", "in", [partner_id]),
            ("active", "=", True),
        ]
        level_config = self.search(domain_patient_specific, limit=1)

        if not level_config:
            domain_generic = [
                ("level_number", "=", level_number),
                ("partner_ids", "=", False),
                ("active", "=", True),
            ]
            level_config = self.search(domain_generic, limit=1)

        if not level_config:
            raise ValidationError(
                _(
                    "No active Level %(level_number)s configuration found "
                    "for patient %(patient_name)s (ID: %(partner_id)s), "
                    "nor a generic configuration for this level."
                )
                % {
                    "level_number": level_number,
                    "patient_name": patient.name,
                    "partner_id": partner_id,
                }
            )

        level_data = level_config.get_level_data_for_unity(
            partner_id_value=patient.id, partner_name_value=patient.name
        )

        return {
            "success": True,
            "level_data": level_data,
            "message": (
                f"Successfully retrieved Level {level_number} configuration "
                f"for patient {patient.name}"
            ),
        }

    @api.model
    def get_first_lc_active(self):
        """Get the first active level configuration found, without patient filtering."""
        domain = [("active", "=", True)]
        level_config = self.search(domain, limit=1, order="level_number ASC, id ASC")

        if not level_config:
            return {
                "success": False,
                "level_data": {},
                "message": "No active level configuration found.",
            }

        level_data = level_config.get_data_for_unity()

        return {
            "success": True,
            "level_data": level_data,
            "message": (
                "Successfully retrieved first active level configuration: "
                f"{level_config.name}"
            ),
        }
