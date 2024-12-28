import base64
import logging
from io import BytesIO

import face_recognition
import numpy as np
from PIL import Image, UnidentifiedImageError

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    face_encoding = fields.Binary(compute="_compute_face_encoding", store=True)

    @api.depends("image_512")
    def _compute_face_encoding(self):
        for user in self.filtered("image_512"):
            try:
                image_data = base64.b64decode(user.image_512)
                image = Image.open(BytesIO(image_data))

                if image.mode in ("RGBA", "LA") or (
                    image.mode == "P" and "transparency" in image.info
                ):
                    image = image.convert("RGBA")
                    image = Image.alpha_composite(
                        Image.new("RGB", image.size, (255, 255, 255)), image
                    )
                else:
                    image = image.convert("RGB")

                image_np = np.array(image)
                encodings = face_recognition.face_encodings(image_np)
                if encodings:
                    user.face_encoding = base64.b64encode(encodings[0].tobytes())
                else:
                    user.face_encoding = False

            except (UnidentifiedImageError, ValueError, RuntimeError) as e:
                _logger.info(f"Failed to process image for user {user.id}: {e}")
                user.face_encoding = False
