from odoo import _, models
from odoo.exceptions import AccessDenied


class ResUsers(models.Model):
    _inherit = "res.users"

    def _check_credentials(self, password, env):
        user = self.env.user
        if not user.self_managed:
            raise AccessDenied(
                _("Access denied: Your profile is not marked as self-managed.")
            )
        return super()._check_credentials(password, env)
