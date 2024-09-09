from odoo import fields, models
from ..routers import router
from odoo.addons.fastapi.dependencies import authenticated_partner_impl
from ..dependencies import authenticated_partner_from_jwt
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("out_of_reality", "Out of reality")], ondelete={"out_of_reality": "cascade"}
    )

    def _get_fastapi_routers(self):
        if self.app == "out_of_reality":
            return [router]
        return super()._get_fastapi_routers()

    def _get_app(self):
        app = super()._get_app()
        if self.app == "out_of_reality":
            app.dependency_overrides[
                authenticated_partner_impl
            ] = authenticated_partner_from_jwt
        return app

    def _get_fastapi_app_middlewares(self) -> list[Middleware]:
        middlewares = super()._get_fastapi_app_middlewares()

        cors_middleware = Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        middlewares.append(cors_middleware)

        return middlewares
