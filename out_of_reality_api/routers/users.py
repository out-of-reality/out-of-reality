from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt

from odoo.api import Environment
from odoo.exceptions import AccessDenied

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import authenticated_partner, odoo_env

from ..controllers.main import FaceIDFastAPIController
from ..schemas import UserData, UserFaceIDLogin, UserLogin, UserResponse

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(tags=["users"])


def create_access_token(data: dict, secret_key: str):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/login", response_model=UserResponse)
def login(
    user_login: UserLogin, env: Annotated[Environment, Depends(odoo_env)]
) -> UserResponse:
    username = user_login.username
    password = user_login.password

    secret_key = env["ir.config_parameter"].sudo().get_param("jwt.secret_key")
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Secret key is not configured in the system",
        )

    try:
        uid = (
            env["res.users"]
            .sudo()
            .authenticate(
                db=env.cr.dbname, login=username, password=password, user_agent_env=None
            )
        )
    except AccessDenied as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from err

    user = env["res.users"].browse(uid)

    access_token = create_access_token(data={"sub": username}, secret_key=secret_key)

    return UserResponse(
        id=user.id, name=user.name, email=user.email, access_token=access_token
    )


@router.get("/whoami", response_model=UserData)
def whoami(partner: Annotated[Partner, Depends(authenticated_partner)]) -> UserData:
    return UserData(name=partner.name)


@router.post("/faceid_login", response_model=UserResponse)
def faceid_login(
    user_login: UserFaceIDLogin, env: Annotated[Environment, Depends(odoo_env)]
) -> UserResponse:
    image = user_login.image

    try:
        faceid_controller = FaceIDFastAPIController()
        response = faceid_controller.verify_face(image)

        if response.get("success"):
            matched_user = response.get("user")

            access_token = create_access_token(
                data={"sub": matched_user.login},
                secret_key=env["ir.config_parameter"]
                .sudo()
                .get_param("jwt.secret_key"),
            )

            return UserResponse(
                id=matched_user.id,
                name=matched_user.name,
                email=matched_user.email,
                access_token=access_token,
            )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="FaceID verification failed",
        ) from err
