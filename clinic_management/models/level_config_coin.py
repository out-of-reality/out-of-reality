from odoo import fields, models


class LevelCoinPoseLine(models.Model):
    _name = "level.coin.pose.line"
    _description = "Level Coin Pose Sequence Line"
    _order = "sequence"

    level_config_id = fields.Many2one(
        "level.configuration",
        string="Level Configuration",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(
        help="Order of the coin pose during gameplay.",
    )
    pose_id = fields.Many2one(
        "pose.definition",
        string="Coin Pose",
        required=True,
        ondelete="cascade",
        help="The specific pose for this coin.",
    )
