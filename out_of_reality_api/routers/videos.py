import base64
import logging
import os
import re
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from odoo.api import Environment

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.clinic_management.utils.video_annotator import (
    convert_video_to_h264_ffmpeg,
)
from odoo.addons.fastapi.dependencies import authenticated_partner, odoo_env

_logger = logging.getLogger(__name__)

router = APIRouter(tags=["videos"])


@router.post("/upload/")
def upload_video(
    partner: Annotated[Partner, Depends(authenticated_partner)],
    video: Annotated[UploadFile, File()],
    env: Annotated[Environment, Depends(odoo_env)],
):
    if not video.filename or not video.filename.lower().endswith(".mp4"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only .mp4 files are allowed.")

    sanitized_name = re.sub(r"[^\w\d_\-\.]", "_", video.filename)
    temp_input_path = f"/tmp/{sanitized_name}"
    final_output_path = f"/tmp/final_{sanitized_name}"

    try:
        with open(temp_input_path, "wb") as f:
            f.write(video.file.read())

        if not convert_video_to_h264_ffmpeg(temp_input_path, final_output_path):
            _logger.error(
                f"Video conversion for {sanitized_name} failed. "
                f"See previous logs for details."
            )
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Video conversion failed on the server.",
            )

        with open(final_output_path, "rb") as f:
            video_base64 = base64.b64encode(f.read()).decode("utf-8")

        env["clinic.game.session"].sudo().create(
            {
                "video": video_base64,
                "filename": os.path.basename(final_output_path),
                "patient_id": partner.id,
            }
        )

        return {"status": "uploaded", "filename": os.path.basename(final_output_path)}

    except HTTPException:
        raise
    except Exception as e:
        _logger.error(f"Unhandled error in upload_video: {e}", exc_info=True)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Unexpected server error: {e}"
        ) from e
    finally:
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)
        if os.path.exists(final_output_path):
            os.remove(final_output_path)
