from odoo.addons.auth_faceid.controllers.main import FaceIDLoginController
from odoo.http import request


class FaceIDFastAPIController(FaceIDLoginController):

    def _login_user(self, user):
        if 'faceid_login' in request.httprequest.url:
            return {'success': True, 'user': user}
        return super()._login_user(user)
