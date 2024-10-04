from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends
from odoo.api import Environment
from odoo.addons.fastapi.dependencies import odoo_env
import base64
import subprocess
import os
from odoo.addons.fastapi.dependencies import authenticated_partner
from odoo.addons.base.models.res_partner import Partner
from typing import Annotated

router = APIRouter(tags=["videos"])


def convert_to_h264(input_file: str, output_file: str):
    conversion_command = [
        'ffmpeg', '-i', input_file, '-vcodec', 'libx264', '-crf', '23', '-preset', 'medium', output_file
    ]
    subprocess.run(conversion_command)


@router.post("/upload/")
def upload_video(
    partner: Annotated[Partner, Depends(authenticated_partner)],
    video: UploadFile = File(...),
    env: Environment = Depends(odoo_env),
):
    try:
        input_file_path = f"/tmp/{video.filename}"
        with open(input_file_path, "wb") as f:
            f.write(video.file.read())

        output_file_path = input_file_path.replace(".avi", ".mp4")
        convert_to_h264(input_file_path, output_file_path)

        with open(output_file_path, "rb") as f:
            video_data = f.read()

        video_base64 = base64.b64encode(video_data).decode('utf-8')

        env['clinic.game.session'].sudo().create({
            'video': video_base64,
            'filename': os.path.basename(output_file_path),
            'patient_id': partner.id
        })

        os.remove(input_file_path)
        os.remove(output_file_path)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving video: {str(e)}",
        )

    return {"status": "uploaded", "partner_id": partner.id}
