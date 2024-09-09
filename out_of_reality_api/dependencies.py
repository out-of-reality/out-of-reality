from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from odoo.api import Environment
from odoo.addons.fastapi.dependencies import odoo_env
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_users import Users
from typing import Annotated

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ALGORITHM = "HS256"


def authenticate_jwt(token: str = Depends(oauth2_scheme), env: Environment = Depends(odoo_env)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        secret_key = env['ir.config_parameter'].sudo().get_param('jwt.secret_key')
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        user = env["res.users"].sudo().search([('login', '=', username)], limit=1)

        if not user:
            raise credentials_exception
        return user

    except JWTError:
        raise credentials_exception


def authenticated_partner_from_jwt(
    user: Annotated[Users, Depends(authenticate_jwt)],
    env: Annotated[Environment, Depends(odoo_env)],
) -> Partner:
    return env["res.partner"].browse(user.sudo().partner_id.id)
