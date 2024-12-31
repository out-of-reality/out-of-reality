from odoo import api, models, fields
import mediapipe as mp
import numpy as np
import cv2
import tempfile
import os
import json
import base64
import matplotlib.pyplot as plt
from enum import Enum

class AngulosArticulares(Enum):
    CODO_DERECHO = ('RIGHT_SHOULDER', 'RIGHT_ELBOW', 'RIGHT_WRIST')
    CODO_IZQUIERDO = ('LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST')
    HOMBRO_DERECHO = ('RIGHT_HIP', 'RIGHT_SHOULDER', 'RIGHT_ELBOW')
    HOMBRO_IZQUIERDO = ('LEFT_HIP', 'LEFT_SHOULDER', 'LEFT_ELBOW')
    RODILLA_DERECHA = ('RIGHT_HIP', 'RIGHT_KNEE', 'RIGHT_ANKLE')
    RODILLA_IZQUIERDA = ('LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE')
    CADERA_DERECHA = ('RIGHT_SHOULDER', 'RIGHT_HIP', 'RIGHT_KNEE')
    CADERA_IZQUIERDA = ('LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_KNEE')
    TOBILLO_DERECHO = ('RIGHT_KNEE', 'RIGHT_ANKLE', 'RIGHT_FOOT_INDEX')
    TOBILLO_IZQUIERDO = ('LEFT_KNEE', 'LEFT_ANKLE', 'LEFT_FOOT_INDEX')

class ClinicGameSession(models.Model):
    _name = 'clinic.game.session'
    _description = 'Clinic Game Session'
    _inherit = ['abstract.mpld3.parser']
    _rec_name = 'patient_id'

    patient_id = fields.Many2one('res.partner', string="Paciente")
    video = fields.Binary(string="Archivo de Video")
    filename = fields.Char(string="Nombre de Archivo")
    session_date = fields.Date(default=fields.Datetime.now, string="Fecha de Sesión")

    landmark_data = fields.Text(string="Landmark Data")
    angle_data = fields.Text(string="Angle Data")
    grafico_1 = fields.Json(string="Gráfico 1", compute='_compute_grafico_1')
    grafico_2 = fields.Json(string="Gráfico 2", compute='_compute_grafico_2')

    angle_selection_1 = fields.Selection(
        [(angle.name, angle.name) for angle in AngulosArticulares],
        string="Ángulo 1",
        default='CODO_DERECHO'
    )
    angle_selection_2 = fields.Selection(
        [(angle.name, angle.name) for angle in AngulosArticulares],
        string="Ángulo 2",
        default='CODO_IZQUIERDO'
    )

    @api.model
    def create(self, vals):
        session = super(ClinicGameSession, self).create(vals)
        if vals.get('video'):
            session.process_video()
        return session

    def process_video(self):
        # Save video to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(base64.b64decode(self.video))
            video_path = temp_video.name

        # Initialize MediaPipe Pose
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.8, min_tracking_confidence=0.75)
        
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
                landmarks_frame = [[lm.x, lm.y, lm.z] for lm in results.pose_world_landmarks.landmark]
                landmark_data.append(landmarks_frame)
                for angle_enum in AngulosArticulares:
                    try:
                        a, b, c = [landmarks_frame[mp_pose.PoseLandmark[landmark].value] for landmark in angle_enum.value]
                        angle = self.calculate_angle_3d(a, b, c)
                        angle_data[angle_enum.name].append(angle)
                    except Exception:
                        print(f"Error al calcular el ángulo {angle_enum.name}")
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

        # Cargar los datos JSON directamente desde los campos `landmark_data` y `angle_data`
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
            90 if "CODO" in angle_selection else
            160 if "RODILLA" in angle_selection or "HIP" in angle_selection else
            0 if "COLUMNA" in angle_selection else None
        )

        # Crear gráfico
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.suptitle(f"Evolución del Ángulo de {angle_selection}")
        ax.plot(time_data, angle_data, label=angle_selection)
        if target is not None:
            ax.plot(time_data, [target] * len(time_data), color='r', linestyle='--', label=f'Objetivo {target}°')
        ax.set_xlabel('Tiempo (s)')
        ax.set_ylabel('Ángulo (°)')
        ax.legend()

        # Convertir a JSON para mpld3
        mpld3_chart = self.convert_figure_to_json(fig)
        plt.close(fig)  # Cerrar figura para liberar memoria
        return mpld3_chart