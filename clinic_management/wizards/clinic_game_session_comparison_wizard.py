import logging

import matplotlib.pyplot as plt

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..utils import chart_generator

_logger = logging.getLogger(__name__)


class ClinicGameSessionComparisonWizard(models.TransientModel):
    _name = "clinic.game.session.comparison.wizard"
    _description = "Wizard to Compare Clinic Game Sessions"
    _inherit = "abstract.mpld3.parser"

    session_ids = fields.Many2many(
        "clinic.game.session",
        string="Sessions to Compare",
        required=True,
        domain="[('state', '=', 'processed'), ('angle_data', '!=', False)]",
    )
    angle_tag_ids = fields.Many2many(
        "clinic.joint.angle.tag",
        "clinic_game_session_cmpwiz_angle_tag_rel",
        "wizard_id",
        "tag_id",
        string="Angles to Compare",
        required=True,
    )
    comparison_chart_data = fields.Json(
        readonly=True,
        compute="_compute_comparison_chart_data",
    )

    @api.constrains("session_ids")
    def _check_sessions_valid(self):
        for wizard in self:
            if not wizard.session_ids:
                raise ValidationError(_("No sessions selected."))
            if wizard.session_ids.filtered(lambda r: r.state != "processed"):
                raise ValidationError(_("All selected sessions must be processed."))

    @api.depends_context("fullscreen_chart")
    @api.depends("session_ids", "angle_tag_ids")
    def _compute_comparison_chart_data(self):
        for wizard in self:
            if not wizard.session_ids or not wizard.angle_tag_ids:
                wizard.comparison_chart_data = {}
                continue

            prepared_data = wizard._prepare_data_for_chart()

            fig = chart_generator.build_comparison_figure(
                prepared_data, fullscreen=self.env.context.get("fullscreen_chart")
            )

            if fig:
                wizard.comparison_chart_data = wizard._convert_figure(fig)
            else:
                wizard.comparison_chart_data = {}

    def _prepare_data_for_chart(self):
        chart_data = []
        for angle_tag in self.angle_tag_ids:
            series_data = []
            for session in self.session_ids:
                time_vals, angle_vals, session_label = self._extract_session_data(
                    session, angle_tag
                )
                series_data.append(
                    {
                        "label": session_label,
                        "x": time_vals,
                        "y": angle_vals,
                    }
                )
            chart_data.append(
                {
                    "title": angle_tag.display_name_tag,
                    "series": series_data,
                }
            )
        return chart_data

    def _extract_session_data(self, session, angle_tag):
        if not session.angle_data or not session.video_fps or session.video_fps <= 0:
            return [], [], ""

        all_angles = session.angle_data
        if not isinstance(all_angles, dict):
            _logger.warning(
                "Could not parse angle_data for session "
                f"{session.id} in comparison wizard."
            )
            return [], [], ""

        values = all_angles.get(angle_tag.name, [])
        if not values:
            return [], [], ""

        time_vals = [
            idx / session.video_fps for idx, v in enumerate(values) if v is not None
        ]
        angle_vals = [v for v in values if v is not None]
        session_label = (
            f"{session.patient_id.name} - "
            f"{session.session_date.strftime('%Y-%m-%d')}"
        )
        return time_vals, angle_vals, session_label

    def _convert_figure(self, fig):
        mpld3_data_dict = {}
        try:
            mpld3_data_dict = self.convert_figure_to_json(fig)
        except Exception as e:
            _logger.error(
                f"Error converting comparison chart to mpld3 for wizard {self.id}: {e}",
                exc_info=True,
            )
        finally:
            if plt.fignum_exists(fig.number):
                plt.close(fig)
        return mpld3_data_dict

    def action_open_fullscreen_chart(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Full Comparison Chart"),
            "res_model": "clinic.game.session.comparison.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "view_id": self.env.ref(
                "clinic_management.view_clinic_game_session_comparison_wizard_fullchart_form"
            ).id,
            "target": "current",
            "context": dict(fullscreen_chart=True),
        }
