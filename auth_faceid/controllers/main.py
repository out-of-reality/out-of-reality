import base64
from io import BytesIO

import face_recognition
import numpy as np
from PIL import Image

from odoo import _, http
from odoo.exceptions import AccessDenied
from odoo.http import request


class FaceIDLoginController(http.Controller):
    @http.route("/web/login/verify_face", type="json", auth="public", methods=["POST"])
    def verify_face(self, image):
        try:
            image_data = base64.b64decode(image.split(",")[1])
            captured_image = np.array(Image.open(BytesIO(image_data)).convert("RGB"))

            captured_face_encodings = face_recognition.face_encodings(captured_image)
            if not captured_face_encodings:
                return {
                    "success": False,
                    "message": _("No face detected in the captured image."),
                }

            captured_face_encoding = captured_face_encodings[0]

            users = (
                request.env["res.users"].sudo().search([("face_encoding", "!=", False)])
            )

            if not users:
                return {
                    "success": False,
                    "message": _("No users with registered face encodings found."),
                }

            user_face_encodings = [
                np.frombuffer(base64.b64decode(user.face_encoding), dtype=np.float64)
                for user in users
            ]
            matches = face_recognition.compare_faces(
                user_face_encodings, captured_face_encoding
            )

            matched_user = next(
                (user for user, match in zip(users, matches, strict=True) if match),
                None,
            )

            if matched_user:
                return self._login_user(matched_user)

            return {
                "success": False,
                "message": _("No match found for the captured face."),
            }

        except AccessDenied:
            return {"success": False, "message": _("Access denied.")}
        except Exception as e:
            return {"success": False, "message": _(str(e))}

    def _login_user(self, user):
        try:
            request.session.uid = user.id
            session_token = user._compute_session_token(request.session.sid)
            request.session.session_token = session_token

            return {
                "success": True,
                "message": _(
                    "User %(user)s authenticated successfully.",
                    user=user.partner_id.name,
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "message": _("Session creation error: %(error)s", error=str(e)),
            }
