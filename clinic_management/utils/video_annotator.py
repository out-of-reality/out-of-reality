import base64
import json
import logging
import os
import subprocess
import tempfile
import time

import cv2
import matplotlib.pyplot as plt
import mediapipe as mp

from .video_processor import JointAngles

_logger = logging.getLogger(__name__)


def convert_video_to_h264_ffmpeg(input_filepath, output_filepath):
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_filepath,
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-vcodec",
        "libx264",
        "-crf",
        "23",
        "-preset",
        "ultrafast",
        output_filepath,
    ]
    context = (
        f"ffmpeg (input: {os.path.basename(input_filepath)}, "
        f"output: {os.path.basename(output_filepath)})"
    )
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        stdout, stderr = process.communicate(timeout=300)

        if process.returncode != 0:
            err_msg = (
                f"{context} failed.\nReturn: {process.returncode}\n"
                f"Stderr: {stderr}\nStdout: {stdout}"
            )
            _logger.error(err_msg)
            return False

        if not os.path.exists(output_filepath) or os.path.getsize(output_filepath) == 0:
            err_msg = (
                f"{context} resulted in empty/missing file.\n"
                f"Stderr: {stderr}\nStdout: {stdout}"
            )
            _logger.error(err_msg)
            return False

    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        err_msg = f"{context} timed out.\nStderr: {stderr}\nStdout: {stdout}"
        _logger.error(err_msg)
        return False
    except Exception as e:
        err_msg = f"Exception during {context}: {str(e)}"
        _logger.error(err_msg, exc_info=True)
        return False
    return True


def _draw_angle_on_frame(
    frame,
    angle_name_key,
    pose_landmarks,
    frame_idx,
    frame_width,
    frame_height,
    all_angles_over_time,
    color,
    mp_pose,
):
    try:
        angle_def = getattr(JointAngles, angle_name_key).value
        p1_n, p2_n, p3_n = angle_def[0], angle_def[1], angle_def[2]

        lm1 = pose_landmarks.landmark[mp_pose.PoseLandmark[p1_n].value]
        lm2 = pose_landmarks.landmark[mp_pose.PoseLandmark[p2_n].value]
        lm3 = pose_landmarks.landmark[mp_pose.PoseLandmark[p3_n].value]

        if not (lm1.visibility > 0.3 and lm2.visibility > 0.3 and lm3.visibility > 0.3):
            return

        pt1 = (int(lm1.x * frame_width), int(lm1.y * frame_height))
        pt2 = (int(lm2.x * frame_width), int(lm2.y * frame_height))
        pt3 = (int(lm3.x * frame_width), int(lm3.y * frame_height))

        line_color = (0, 255, 0)
        circle_color = (0, 0, 255)
        cv2.line(frame, pt1, pt2, line_color, 2)
        cv2.line(frame, pt2, pt3, line_color, 2)
        cv2.circle(frame, pt1, 5, circle_color, -1)
        cv2.circle(frame, pt2, 8, circle_color, -1)
        cv2.circle(frame, pt3, 5, circle_color, -1)

        current_angle = None
        if (
            angle_name_key in all_angles_over_time
            and all_angles_over_time[angle_name_key]
            and frame_idx < len(all_angles_over_time[angle_name_key])
        ):
            current_angle = all_angles_over_time[angle_name_key][frame_idx]

        if current_angle is not None:
            text = f"{current_angle:.0f}"
            text_x = max(10, min(pt2[0] + 20, frame_width - 70))
            text_y = max(30, min(pt2[1] - 20, frame_height - 10))
            cv2.putText(
                frame,
                text,
                (text_x, text_y),
                cv2.FONT_HERSHEY_TRIPLEX,
                0.8,
                color,
                2,
                cv2.LINE_AA,
            )
    except (AttributeError, IndexError, KeyError) as e:
        _logger.debug(
            "Skipping drawing angle %s for frame %s due to missing data: %s",
            angle_name_key,
            frame_idx,
            e,
        )


def generate_annotated_video(
    original_video_path,
    angle_data_json,
    selected_angle_names,
    video_fps,
    original_filename,
):
    opencv_out_path, ffmpeg_out_path = "", ""
    try:
        cap = cv2.VideoCapture(original_video_path)
        if not cap.isOpened():
            raise OSError("Could not open original video for annotation.")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if not (width > 0 and height > 0):
            cap.release()
            raise ValueError("Invalid video dimensions.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".avi") as tmp_cv_out:
            opencv_out_path = tmp_cv_out.name

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out_writer = cv2.VideoWriter(
            opencv_out_path, fourcc, video_fps, (width, height)
        )
        if not out_writer.isOpened():
            cap.release()
            raise OSError("Could not initialize OpenCV VideoWriter.")

        all_angles_data = json.loads(angle_data_json)
        mp_pose = mp.solutions.pose
        cmap = plt.get_cmap("tab10")
        frame_idx = 0

        with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as pose_tracker:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb_img.flags.writeable = False
                results = pose_tracker.process(rgb_img)
                annotated_img = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)

                if results.pose_landmarks:
                    for i, angle_key in enumerate(selected_angle_names):
                        plot_color_rgba = cmap(i % cmap.N)
                        text_color_bgr = (
                            int(plot_color_rgba[2] * 255),
                            int(plot_color_rgba[1] * 255),
                            int(plot_color_rgba[0] * 255),
                        )
                        _draw_angle_on_frame(
                            annotated_img,
                            angle_key,
                            results.pose_landmarks,
                            frame_idx,
                            width,
                            height,
                            all_angles_data,
                            text_color_bgr,
                            mp_pose,
                        )

                out_writer.write(annotated_img)
                frame_idx += 1

        cap.release()
        out_writer.release()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_ff_out:
            ffmpeg_out_path = tmp_ff_out.name

        conversion_ok = convert_video_to_h264_ffmpeg(opencv_out_path, ffmpeg_out_path)
        if not conversion_ok:
            raise Exception("FFMPEG conversion failed.")

        with open(ffmpeg_out_path, "rb") as vf:
            video_b64 = base64.b64encode(vf.read())

        ts = str(int(time.time()))
        base_fn = os.path.splitext(original_filename or "video")[0]
        fn_annotated = f"{base_fn}_annotated_{ts}.mp4"

        return video_b64, fn_annotated

    finally:
        for p in [opencv_out_path, ffmpeg_out_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError as e:
                    _logger.error("Error removing temporary file %s: %s", p, e)
