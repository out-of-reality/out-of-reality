from odoo import fields, models


class LevelCoinPoseLine(models.Model):
    _name = "level.coin.pose.line"
    _description = "Level Coin Pose Sequence Line"
    _order = "sequence, id"  # Important for maintaining order

    level_config_id = fields.Many2one(
        "level.configuration",
        string="Level Configuration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(
        default=10,  # Standard Odoo default sequence value
        help="Order of the coin pose in the challenge.",
    )
    pose_id = fields.Many2one(
        "pose.definition",
        string="Coin Pose",
        required=True,
        domain=[("active", "=", True)],
        ondelete="cascade",
        help="The specific pose for this coin.",
    )
