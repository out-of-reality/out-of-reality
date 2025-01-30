import json
from enum import Enum

import cv2
import mediapipe as mp
import numpy as np


class JointAngles(Enum):
    RIGHT_ELBOW = ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST")
    LEFT_ELBOW = ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST")
    RIGHT_SHOULDER = ("RIGHT_HIP", "RIGHT_SHOULDER", "RIGHT_ELBOW")
    LEFT_SHOULDER = ("LEFT_HIP", "LEFT_SHOULDER", "LEFT_ELBOW")
    RIGHT_KNEE = ("RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE")
    LEFT_KNEE = ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE")
    RIGHT_HIP = ("RIGHT_SHOULDER", "RIGHT_HIP", "RIGHT_KNEE")
    LEFT_HIP = ("LEFT_SHOULDER", "LEFT_HIP", "LEFT_KNEE")
    RIGHT_ANKLE = ("RIGHT_KNEE", "RIGHT_ANKLE", "RIGHT_FOOT_INDEX")
    LEFT_ANKLE = ("LEFT_KNEE", "LEFT_ANKLE", "LEFT_FOOT_INDEX")


def _calculate_angle_3d(a, b, c):
    vec_a, vec_b, vec_c = np.array(a), np.array(b), np.array(c)
    ba, bc = vec_a - vec_b, vec_c - vec_b
    dot_product = np.dot(ba, bc)
    magnitude_ba, magnitude_bc = np.linalg.norm(ba), np.linalg.norm(bc)
    if magnitude_ba == 0 or magnitude_bc == 0:
        return 0.0
    cosine_angle = np.clip(dot_product / (magnitude_ba * magnitude_bc), -1.0, 1.0)
    return np.degrees(np.arccos(cosine_angle))


def process_video_from_path(video_path):
    mp_pose = mp.solutions.pose
    all_world_landmarks_over_time = []
    processed_frames_data = []
    frame_count = 0

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise OSError(f"No se pudo abrir el archivo de video en la ruta: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as pose_detector:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_rgb.flags.writeable = False
            results = pose_detector.process(image_rgb)
            image_rgb.flags.writeable = True

            current_frame_angles = {}
            current_world_landmarks_frame = []

            if results.pose_world_landmarks:
                landmarks_list = results.pose_world_landmarks.landmark
                current_world_landmarks_frame = [
                    [lm.x, lm.y, lm.z, lm.visibility] for lm in landmarks_list
                ]
                all_world_landmarks_over_time.append(current_world_landmarks_frame)

                for angle_enum in JointAngles:
                    try:
                        p_indices = [
                            mp_pose.PoseLandmark[name].value
                            for name in angle_enum.value
                        ]
                        points = [
                            current_world_landmarks_frame[idx][:3] for idx in p_indices
                        ]
                        current_frame_angles[angle_enum.name] = _calculate_angle_3d(
                            *points
                        )
                    except (IndexError, KeyError):
                        current_frame_angles[angle_enum.name] = None
            else:
                all_world_landmarks_over_time.append([])

            processed_frames_data.append(
                {"frame_number": frame_count, "angles": current_frame_angles}
            )

    cap.release()

    landmark_json = json.dumps(all_world_landmarks_over_time)
    all_angles_over_time = {
        angle.name: [fd["angles"].get(angle.name) for fd in processed_frames_data]
        for angle in JointAngles
    }
    angle_json = json.dumps(all_angles_over_time)

    return fps, landmark_json, angle_json
