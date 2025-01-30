import base64
import json
import logging
import os
import tempfile
from enum import Enum

import cv2
import matplotlib.pyplot as plt
import mediapipe as mp
import numpy as np

from odoo import _, api, fields, http, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AngulosArticulares(Enum):
    CODO_DERECHO = ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST")
    CODO_IZQUIERDO = ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST")
    HOMBRO_DERECHO = ("RIGHT_HIP", "RIGHT_SHOULDER", "RIGHT_ELBOW")
    HOMBRO_IZQUIERDO = ("LEFT_HIP", "LEFT_SHOULDER", "LEFT_ELBOW")
    RODILLA_DERECHA = ("RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE")
    RODILLA_IZQUIERDA = ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE")
    CADERA_DERECHA = ("RIGHT_SHOULDER", "RIGHT_HIP", "RIGHT_KNEE")
    CADERA_IZQUIERDA = ("LEFT_SHOULDER", "LEFT_HIP", "LEFT_KNEE")
    TOBILLO_DERECHO = ("RIGHT_KNEE", "RIGHT_ANKLE", "RIGHT_FOOT_INDEX")
    TOBILLO_IZQUIERDO = ("LEFT_KNEE", "LEFT_ANKLE", "LEFT_FOOT_INDEX")


class ClinicGameSession(models.Model):
    _name = "clinic.game.session"
    _description = "Clinic Game Session"
    _rec_name = "patient_id"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "portal.mixin",
        "abstract.mpld3.parser",
    ]

    patient_id = fields.Many2one(
        "res.partner", required=True, domain=[("partner_type", "=", "patient")]
    )
    video = fields.Binary()
    filename = fields.Char()
    session_date = fields.Date(default=fields.Datetime.now)
    state = fields.Selection(
        [("new", "New"), ("done", "Done")], default="new", tracking=True
    )
    feedback = fields.Html()
    landmark_data = fields.Text()
    angle_data = fields.Text()
    grafico_1 = fields.Json(compute="_compute_grafico_1")
    grafico_2 = fields.Json(compute="_compute_grafico_2")

    angle_selection_1 = fields.Selection(
        [(angle.name, angle.name) for angle in AngulosArticulares],
        string="Ángulo 1",
        default="CODO_DERECHO",
    )
    angle_selection_2 = fields.Selection(
        [(angle.name, angle.name) for angle in AngulosArticulares],
        string="Ángulo 2",
        default="CODO_IZQUIERDO",
    )

    def _message_get_suggested_recipients(self):
        res = super()._message_get_suggested_recipients()
        patient = self.patient_id
        if patient.self_managed:
            self._message_add_suggested_recipient(res, partner=patient)

        linked_partners = patient.patient_link_ids.mapped("user_id.partner_id")
        for partner in linked_partners:
            self._message_add_suggested_recipient(res, partner=partner)
        return res

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
        if self.env.context.get("mark_gs_as_sent"):
            self.filtered(lambda x: x.state == "new").write({"state": "done"})
        if (
            self._name == "clinic.game.session"
            and http.request
            and http.request.env.user.has_group("base.group_portal")
        ):
            self = self.sudo()
            self._subscribe_partners()
        return super().message_post(**kwargs)

    @api.model_create_multi
    def create(self, vals_list):
        record = super().create(vals_list)

        if record.video:
            record.process_video()

        kinesiologists = record.patient_id.patient_link_ids.filtered(
            lambda link: link.user_id.partner_id.partner_type == "kinesiologist"
        ).mapped("user_id")

        for kinesiologist in kinesiologists:
            record.activity_schedule(
                activity_type_id=self.env.ref("mail.mail_activity_data_todo").id,
                user_id=kinesiologist.id,
                summary=_("Review game session for %s") % record.patient_id.name,
                date_deadline=fields.Date.today(),
            )

        return record

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

    def process_video(self):
        # Save video to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(base64.b64decode(self.video))
            video_path = temp_video.name

        # Initialize MediaPipe Pose
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.8,
            min_tracking_confidence=0.75,
        )

        cap = cv2.VideoCapture(video_path)

        landmark_data = []
        angle_data = {angle.name: [] for angle in AngulosArticulares}

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Process frame with MediaPipe Pose
            results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if results.pose_world_landmarks:
                landmarks_frame = [
                    [lm.x, lm.y, lm.z] for lm in results.pose_world_landmarks.landmark
                ]
                landmark_data.append(landmarks_frame)
                for angle_enum in AngulosArticulares:
                    try:
                        a, b, c = (
                            landmarks_frame[mp_pose.PoseLandmark[landmark].value]
                            for landmark in angle_enum.value
                        )
                        angle = self.calculate_angle_3d(a, b, c)
                        angle_data[angle_enum.name].append(angle)
                    except Exception:
                        _logger.info(f"Error al calcular el ángulo {angle_enum.name}")
                        continue

        cap.release()
        os.remove(video_path)

        # Save data to fields as JSON
        self.landmark_data = json.dumps(landmark_data)
        self.angle_data = json.dumps(angle_data)

    @staticmethod
    def calculate_angle_3d(a, b, c):
        ab = np.array(a) - np.array(b)
        bc = np.array(c) - np.array(b)
        ab_u = ab / np.linalg.norm(ab)
        bc_u = bc / np.linalg.norm(bc)
        dot = np.dot(ab_u, bc_u)
        angulo_rad = np.arccos(np.clip(dot, -1.0, 1.0))
        return np.degrees(angulo_rad)

    def _compute_grafico_1(self):
        for record in self:
            record.grafico_1 = record.generar_grafico(record.angle_selection_1)

    def _compute_grafico_2(self):
        for record in self:
            record.grafico_2 = record.generar_grafico(record.angle_selection_2)

    def generar_grafico(self, angle_selection):
        if not self.landmark_data or not self.angle_data:
            return json.dumps({})

        # Cargar los datos JSON directamente desde los campos
        # `landmark_data` y `angle_data`
        landmarks_data = json.loads(self.landmark_data)
        angles_data = json.loads(self.angle_data)

        # Obtener el tiempo en base a la longitud de los datos de landmarks
        time_data = list(range(len(landmarks_data)))

        # Seleccionar el ángulo para graficar
        angle_data = angles_data.get(angle_selection, [])
        if not angle_data:
            return json.dumps({})

        # Definir el objetivo en función del ángulo seleccionado
        target = (
            90
            if "CODO" in angle_selection
            else 160
            if "RODILLA" in angle_selection or "HIP" in angle_selection
            else 0
            if "COLUMNA" in angle_selection
            else None
        )

        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.suptitle(f"Evolución del Ángulo de {angle_selection}")
        ax.plot(time_data, angle_data, label=angle_selection)
        if target is not None:
            ax.plot(
                time_data,
                [target] * len(time_data),
                color="r",
                linestyle="--",
                label=f"Objetivo {target}°",
            )
        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Ángulo (°)")
        ax.legend()

        # Convertir a JSON para mpld3
        mpld3_chart = self.convert_figure_to_json(fig)
        plt.close(fig)  # Cerrar figura para liberar memoria
        return mpld3_chart
