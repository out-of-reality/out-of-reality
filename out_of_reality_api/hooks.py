import secrets


def post_init_hook(env):
    config_param = env['ir.config_parameter'].sudo()
    if not config_param.get_param('jwt.secret_key'):
        secret_key = secrets.token_urlsafe(32)
        config_param.set_param('jwt.secret_key', secret_key)
