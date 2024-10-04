import base64
import os
import re
import subprocess
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from odoo.api import Environment

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import authenticated_partner, odoo_env

router = APIRouter(tags=["videos"])


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^\w\d_\-\.]", "_", filename)


def convert_to_h264(input_file: str, output_file: str):
    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_file,
        "-vf",
        "scale=1280:-2",
        "-vcodec",
        "libx264",
        "-crf",
        "23",
        "-preset",
        "medium",
        output_file,
    ]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    process.wait()
    if process.returncode != 0 or not os.path.exists(output_file):
        raise RuntimeError("ffmpeg failed")


@router.post("/upload/")
def upload_video(
    partner: Annotated[Partner, Depends(authenticated_partner)],
    video: Annotated[UploadFile, File()],
    env: Annotated[Environment, Depends(odoo_env)],
):
    if not video.filename.lower().endswith(".avi"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .avi files are allowed.",
        )

    try:
        sanitized_name = sanitize_filename(video.filename)
        input_path = f"/tmp/{sanitized_name}"
        output_path = input_path.replace(".avi", ".mp4")

        with open(input_path, "wb") as f:
            f.write(video.file.read())

        convert_to_h264(input_path, output_path)

        with open(output_path, "rb") as f:
            video_base64 = base64.b64encode(f.read()).decode("utf-8")

        env["clinic.game.session"].sudo().create(
            {
                "video": video_base64,
                "filename": os.path.basename(output_path),
                "patient_id": partner.id,
            }
        )

        os.remove(input_path)
        os.remove(output_path)

        return {"status": "uploaded", "partner_id": partner.id}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error saving video: {str(e)}"
        ) from e
