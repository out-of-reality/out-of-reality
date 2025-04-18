import json

import requests

from odoo import _, http
from odoo.exceptions import AccessDenied
from odoo.http import request

FACE_SERVICE_URL = "http://face_recognition:5000"


class FaceIDLoginController(http.Controller):
    @http.route(
        "/web/login/verify_face",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def verify_face(self):
        image = json.loads(request.httprequest.data.decode("utf-8")).get("image")
        if not image:
            return {"success": False, "message": _("No image data received.")}

        try:
            response = requests.post(
                f"{FACE_SERVICE_URL}/face_encoding",
                json={"image_b64": image},
                timeout=5,
            )
            if response.status_code != 200:
                return {
                    "success": False,
                    "message": _("No face detected in the captured image."),
                }

            captured_encoding_b64 = response.json().get("encoding")

            users = (
                request.env["res.users"].sudo().search([("face_encoding", "!=", False)])
            )
            if not users:
                return {
                    "success": False,
                    "message": _("No users with registered face encodings found."),
                }

            user_encodings = [user.face_encoding.decode() for user in users]

            response = requests.post(
                f"{FACE_SERVICE_URL}/compare_faces",
                json={
                    "captured_encoding": captured_encoding_b64,
                    "user_encodings": user_encodings,
                },
                timeout=5,
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "message": _("Error comparing faces: %s") % response.text,
                }

            matched_index = response.json().get("matched_index")
            if matched_index is not None:
                matched_user = users[matched_index]
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
