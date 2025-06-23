from odoo import _, http
from odoo.http import request

from ..utils import FaceIDService

FACE_SERVICE_URL = "http://face_recognition:5000"


class FaceIDLoginController(http.Controller):
    @http.route(
        "/web/login/verify_face",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def verify_face(self, image=None, **kwargs):
        result = FaceIDService.identify_user(image, request.env)
        if result["success"]:
            return self._login_user(result["user"])
        return result

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
