import logging

import requests

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

FACE_API_URL = "http://face_recognition:5000"


class ResUsers(models.Model):
    _inherit = "res.users"

    face_encoding = fields.Binary(compute="_compute_face_encoding", store=True)

    @api.depends("image_512")
    def _compute_face_encoding(self):
        users = self.filtered("image_512")
        for user in self.filtered("image_512"):
            try:
                image_b64 = f"data:image/jpeg;base64,{user.image_512.decode()}"
                response = requests.post(
                    f"{FACE_API_URL}/face_encoding",
                    json={"image_b64": image_b64},
                    timeout=5,
                )
                if response.status_code == 200:
                    user.face_encoding = response.json()["encoding"].encode()
                else:
                    user.face_encoding = False
            except Exception as e:
                _logger.info(f"Face encoding error for user {user.id}: {e}")
                user.face_encoding = False
        (self - users).face_encoding = False
