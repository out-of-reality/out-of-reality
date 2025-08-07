import base64
import json
import logging
import os
import tempfile
import warnings

import matplotlib
import matplotlib.pyplot as plt
from mpld3 import plugins

from odoo import _, api, fields, http, models
from odoo.exceptions import UserError, ValidationError

from ..utils import video_annotator, video_processor

_logger = logging.getLogger(__name__)


class ClinicGameSession(models.Model):
    _name = "clinic.game.session"
    _description = "Clinic Game Session"
    _rec_name = "display_name"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "portal.mixin",
        "abstract.mpld3.parser",
    ]
    _order = "session_date desc"

    display_name = fields.Char(
        compute="_compute_display_name", store=True, readonly=False
    )
    patient_id = fields.Many2one(
        "res.partner", required=True, domain=[("partner_type", "=", "patient")]
    )
    video = fields.Binary(attachment=True)
    filename = fields.Char()
    session_date = fields.Datetime(default=fields.Datetime.now)
    state = fields.Selection(
        [
            ("pending_processing", "Pending Processing"),
            ("processing_failed", "Processing Failed"),
            ("processed", "Processed"),
        ],
        string="Status",
        default="pending_processing",
        tracking=True,
    )
    feedback = fields.Html()
    landmark_data = fields.Json(eadonly=True)
    angle_data = fields.Json(readonly=True)
    video_fps = fields.Float(
        string="Video FPS",
        readonly=True,
        help="Frames Per Second of the processed video.",
    )
    selected_angles_for_chart_ids = fields.Many2many(
        "clinic.joint.angle.tag",
        string="Angles for Chart",
        help="Select joint angles to display on the chart(s).",
    )
    chart_display_separate = fields.Boolean(
        string="Display Angles in Separate Charts",
        default=False,
        help=(
            "If checked, each selected angle will be displayed in its own sub-chart. "
            "Otherwise, all selected angles will be overlaid on a single chart."
        ),
    )
    joint_angle_chart_combined = fields.Json(
        compute="_compute_joint_angle_chart_combined",
    )
    video_annotated = fields.Binary(string="Annotated Video", attachment=True)
    filename_annotated = fields.Char(string="Annotated Video Filename", readonly=True)
    annotated_video_state = fields.Selection(
        [
            ("none", "None"),
            ("pending", "Pending Annotation"),
            ("done", "Done"),
            ("failed", "Annotation Failed"),
        ],
        string="Annotation Status",
        default="none",
        readonly=True,
    )

    @api.depends("patient_id", "session_date")
    def _compute_display_name(self):
        for rec in self:
            name = rec.patient_id.name or ""
            date = (
                rec.session_date.strftime("%d/%m/%Y %H:%M") if rec.session_date else ""
            )
            rec.display_name = f"{name} - {date}" if name and date else name or date

    def _subscribe_partners(self):
        for record in self:
            partners_to_subscribe = record.patient_id.patient_link_ids.mapped(
                "user_id.partner_id.id"
            )
            if record.patient_id.self_managed:
                partners_to_subscribe.append(record.patient_id.id)

            if partners_to_subscribe:
                record.message_subscribe(partner_ids=partners_to_subscribe)

    @api.constrains("patient_id")
    def _check_patient(self):
        if self.filtered(lambda x: x.patient_id.partner_type != "patient"):
            raise ValidationError(_("Patients must be of type 'Patient'."))

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        is_portal_user = http.request and http.request.env.user.has_group(
            "base.group_portal"
        )
        if self._name == "clinic.game.session" and is_portal_user:
            self = self.sudo()
        return super().message_post(**kwargs)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._subscribe_partners()
        for record in records:
            kinesiologists = record.patient_id.patient_link_ids.filtered(
                lambda link: link.user_id.partner_id.partner_type == "kinesiologist"
            ).mapped("user_id")

            for kinesiologist in kinesiologists:
                summary = _("Review game session for %s") % record.patient_id.name
                record.activity_schedule(
                    activity_type_id=self.env.ref("mail.mail_activity_data_todo").id,
                    user_id=kinesiologist.id,
                    summary=summary,
                    date_deadline=fields.Date.today(),
                )

        return records

    def _find_mail_template(self):
        self.ensure_one()
        return self.env.ref(
            "clinic_management.email_template_clinic_session", raise_if_not_found=False
        )

    def action_feedback_send(self):
        self.ensure_one()
        mail_template = self._find_mail_template()
        ctx = {
            "default_model": "clinic.game.session",
            "default_res_ids": self.ids,
            "default_template_id": mail_template.id if mail_template else None,
            "default_composition_mode": "comment",
            "mark_gs_as_sent": True,
            "default_email_layout_xmlid": (
                "mail.mail_notification_layout_with_responsible_signature"
            ),
            "force_email": True,
            "user_name": self.env.user.name,
        }
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": ctx,
        }

    def action_preview_game_session(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "new",
            "url": self.get_portal_url(),
        }

    def _compute_access_url(self):
        res = super()._compute_access_url()
        for rec in self:
            rec.access_url = f"/my/game_sessions/{rec.id}"
        return res

    def get_partner_ids_for_notification(self):
        self.ensure_one()
        partner_ids = self.patient_id.patient_link_ids.filtered(
            lambda x: x.user_id.partner_id.partner_type == "guardian"
        ).mapped("user_id.partner_id.id")
        if self.patient_id.self_managed:
            partner_ids.append(self.patient_id.id)
        return partner_ids

    def _process_video_data(self):
        self.ensure_one()
        if not self.video:
            self.state = "processing_failed"
            _logger.warning("Intento de procesar la sesión %s sin video.", self.id)
            return

        temp_video_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp4"
            ) as temp_video_file:
                temp_video_file.write(base64.b64decode(self.video))
                temp_video_path = temp_video_file.name

            fps, landmark_json, angle_json = video_processor.process_video_from_path(
                temp_video_path
            )

            landmark_data = []
            if landmark_json:
                raw_landmarks = json.loads(landmark_json)
                landmark_data = [
                    [[point[0], point[1], point[2]] for point in frame]
                    for frame in raw_landmarks
                ]

            self.write(
                {
                    "video_fps": fps,
                    "landmark_data": landmark_data,
                    "angle_data": json.loads(angle_json) if angle_json else {},
                    "state": "processed",
                }
            )
        except Exception as e:
            _logger.error(
                "Falló el procesamiento de video para la sesión %s: %s",
                self.id,
                e,
                exc_info=True,
            )
            self.state = "processing_failed"
        finally:
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)

    @api.depends(
        "angle_data",
        "selected_angles_for_chart_ids",
        "video_fps",
        "state",
        "chart_display_separate",
    )
    def _compute_joint_angle_chart_combined(self):
        for record in self:
            if (
                record.state == "processed"
                and record.angle_data
                and record.video_fps
                and record.selected_angles_for_chart_ids
            ):
                selected_angle_names = record.selected_angles_for_chart_ids.mapped(
                    "name"
                )
                record.joint_angle_chart_combined = (
                    record._generate_joint_angle_chart(
                        selected_angle_names, record.chart_display_separate
                    )
                    if selected_angle_names
                    else {}
                )
            else:
                record.joint_angle_chart_combined = {}

    def _prepare_chart_figure_axes(self, num_angles, display_separate):
        fig_height = 3 * num_angles
        if display_separate:
            fig, created_axes = plt.subplots(
                nrows=num_angles,
                ncols=1,
                figsize=(12, fig_height if fig_height > 0 else 3),
                sharex=True,
                squeeze=False,
            )
            axes_list = [ax for sublist in created_axes for ax in sublist]
        else:
            fig, main_ax = plt.subplots(figsize=(12, 6))
            axes_list = [main_ax]
        return fig, axes_list

    def _plot_single_angle_series(
        self, ax, angle_name_key, angle_values_series, color, display_separate
    ):
        tag_record = self.env["clinic.joint.angle.tag"].search(
            [("name", "=", angle_name_key)], limit=1
        )
        series_label = (
            tag_record.display_name_tag
            if tag_record
            else angle_name_key.replace("_", " ").title()
        )
        if not angle_values_series:
            if display_separate:
                ax.text(
                    0.5,
                    0.5,
                    f"No data for\n{series_label}",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    fontsize=10,
                )
                ax.set_yticks([])
                ax.set_xticks([])
                ax.set_title(series_label, fontsize=12)
            return False
        valid_angles, time_sec = [], []
        for frame_idx, angle_val in enumerate(angle_values_series):
            if angle_val is not None:
                valid_angles.append(angle_val)
                time_sec.append(frame_idx / self.video_fps)
        if not valid_angles:
            if display_separate:
                ax.text(
                    0.5,
                    0.5,
                    f"No valid data for\n{series_label}",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                    fontsize=10,
                )
                ax.set_yticks([])
                ax.set_xticks([])
                ax.set_title(series_label, fontsize=12)
            return False
        (line,) = ax.plot(
            time_sec, valid_angles, label=series_label, color=color, linewidth=2
        )
        ax.set_ylabel("Angle (°)", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.7)
        if display_separate:
            ax.set_title(series_label, fontsize=12)
            ax.legend([line], [series_label], loc="upper right", fontsize=8)
        scatter = ax.scatter(time_sec, valid_angles, s=15, alpha=0)
        labels = [
            f"{x:.2f} s, {y:.1f}°" for x, y in zip(time_sec, valid_angles, strict=False)
        ]
        plugins.connect(ax.figure, plugins.PointLabelTooltip(scatter, labels=labels))
        return True

    def _finalize_chart_layout_and_legend(self, fig, axes_list, display_separate):
        if display_separate and axes_list:
            axes_list[-1].set_xlabel("Time (s)", fontsize=12)
        elif axes_list:
            main_ax = axes_list[0]
            main_ax.set_xlabel("Time (s)", fontsize=12)
            handles, labels = main_ax.get_legend_handles_labels()
            if handles:
                legend_loc = "upper right"
                bbox_to_anchor = None
                if len(handles) > 4:
                    legend_loc = "center left"
                    bbox_to_anchor = (1.01, 0.5)
                main_ax.legend(
                    handles,
                    labels,
                    loc=legend_loc,
                    fontsize=9,
                    bbox_to_anchor=bbox_to_anchor,
                    borderaxespad=0.0 if bbox_to_anchor else None,
                )
        right_boundary = 0.95
        if not display_separate and axes_list:
            handles, _ = axes_list[0].get_legend_handles_labels()
            if handles and len(handles) > 4:
                right_boundary = 0.85
        try:
            fig.tight_layout(rect=[0, 0.03, right_boundary, 0.95])
        except ValueError:
            _logger.warning("Could not apply tight_layout to chart.", exc_info=True)

    def _generate_joint_angle_chart(self, selected_angle_names, display_separate):
        warnings.filterwarnings(
            "ignore",
            category=matplotlib.MatplotlibDeprecationWarning,
            module="mpld3.mplexporter.utils",
        )
        self.ensure_one()
        if not self.angle_data or not self.video_fps or self.video_fps <= 0:
            return {}

        all_angles_over_time = self.angle_data
        if not isinstance(all_angles_over_time, dict):
            _logger.warning(
                "Chart generation failed: angle_data is not a dictionary for "
                "session %s.",
                self.id,
            )
            return {}
        num_angles = len(selected_angle_names)
        if num_angles == 0:
            return {}
        fig, axes_list = self._prepare_chart_figure_axes(num_angles, display_separate)
        cmap = plt.get_cmap("tab10")
        chart_has_data_overall = False
        for i, angle_name_key in enumerate(selected_angle_names):
            current_ax = axes_list[i] if display_separate else axes_list[0]
            angle_values = all_angles_over_time.get(angle_name_key)
            plot_color = cmap(i % cmap.N)
            if self._plot_single_angle_series(
                current_ax, angle_name_key, angle_values, plot_color, display_separate
            ):
                chart_has_data_overall = True
        if not chart_has_data_overall:
            plt.close(fig)
            return {}
        self._finalize_chart_layout_and_legend(fig, axes_list, display_separate)
        mpld3_chart_json = {}
        try:
            mpld3_chart_json = self.convert_figure_to_json(fig)
        except Exception as e:
            _logger.error(
                "Failed to convert Matplotlib to mpld3 for session %s: %s",
                self.id,
                e,
                exc_info=True,
            )
        finally:
            plt.close(fig)
        return mpld3_chart_json

    @api.model
    def _cron_process_pending_videos(self):
        sessions_to_process = self.search(
            [("state", "=", "pending_processing"), ("video", "!=", False)]
        )
        _logger.info(
            "Cron job: Found %s sessions to process.", len(sessions_to_process)
        )
        for session in sessions_to_process:
            try:
                session._process_video_data()
            except Exception as e:
                _logger.error(
                    "Cron failed processing video for session %s: %s",
                    session.id,
                    e,
                    exc_info=True,
                )
                session.state = "processing_failed"

    def action_generate_annotated_video(self):
        for record in self:
            if record.state != "processed" or not record.video or not record.angle_data:
                raise UserError(
                    _(
                        "The original video must be processed and angle data must "
                        "be available to generate an annotated video."
                    )
                )

            if not record.selected_angles_for_chart_ids:
                raise UserError(
                    _(
                        "Please select at least one angle to visualize in the"
                        " annotated video."
                    )
                )

            record.annotated_video_state = "pending"
            try:
                cron_job_annotate = self.env.ref(
                    "clinic_management.ir_cron_generate_pending_annotated_videos",
                    raise_if_not_found=False,
                )
                if cron_job_annotate:
                    cron_job_annotate._trigger()
            except Exception as e:
                _logger.error(
                    "Failed to trigger annotation cron for session %s: %s",
                    record.id,
                    e,
                    exc_info=True,
                )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Annotation Queued"),
                "message": _(
                    "Annotated video generation has been queued. Please refresh"
                    " the page in a few moments to view the result."
                ),
                "type": "info",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    def _generate_annotated_video_processing(self):
        self.ensure_one()
        temp_video_path = ""
        try:
            selected_angle_names = self.selected_angles_for_chart_ids.mapped("name")

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp4"
            ) as temp_video_file:
                temp_video_file.write(base64.b64decode(self.video))
                temp_video_path = temp_video_file.name

            video_b64, filename_annotated = video_annotator.generate_annotated_video(
                original_video_path=temp_video_path,
                angle_data_json=json.dumps(self.angle_data)
                if self.angle_data
                else "{}",
                selected_angle_names=selected_angle_names,
                video_fps=self.video_fps,
                original_filename=self.filename,
            )

            self.write(
                {
                    "video_annotated": video_b64,
                    "filename_annotated": filename_annotated,
                    "annotated_video_state": "done",
                }
            )

        except Exception as e:
            _logger.error(
                "Falló la anotación de video para la sesión %s: %s",
                self.id,
                e,
                exc_info=True,
            )
            self.write({"annotated_video_state": "failed", "video_annotated": False})
        finally:
            if temp_video_path and os.path.exists(temp_video_path):
                os.remove(temp_video_path)

    @api.model
    def _cron_generate_pending_annotations(self):
        sessions_to_annotate = self.search(
            [
                ("state", "=", "processed"),
                ("annotated_video_state", "=", "pending"),
                ("selected_angles_for_chart_ids", "!=", False),
            ]
        )
        _logger.info(
            "Cron job: Found %s sessions to annotate.", len(sessions_to_annotate)
        )
        for session in sessions_to_annotate:
            try:
                session._generate_annotated_video_processing()
                self.env.registry.clear_all_caches()
            except Exception as e:
                _logger.error(
                    "Cron failed annotating video for session %s: %s",
                    session.id,
                    e,
                    exc_info=True,
                )
                session.annotated_video_state = "failed"
        return True

    def action_compare_sessions(self):
        wizard = self.env["clinic.game.session.comparison.wizard"].create(
            {
                "session_ids": [(6, 0, self.ids)],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": "Compare Game Sessions",
            "res_model": "clinic.game.session.comparison.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }
