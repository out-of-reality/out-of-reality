import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import authenticated_partner, odoo_env

from ..schemas import LevelConfigurationResponse

router = APIRouter(tags=["levels"])


@router.get("/levels/first_active", response_model=LevelConfigurationResponse)
def get_first_level_configuration(
    env: Annotated[Environment, Depends(odoo_env)],
) -> LevelConfigurationResponse:
    try:
        LevelConfigModel = env["level.configuration"].sudo()
        export_data = LevelConfigModel.get_first_level_config()

        if not export_data.get("success") or not export_data.get("level_data"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=export_data.get(
                    "message", "No active level configuration found."
                ),
            )

        return LevelConfigurationResponse(
            success=export_data["success"],
            level_data=export_data["level_data"],
            timestamp=export_data.get("level_data", {}).get("timestamp"),
            message=export_data["message"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(
            "Unexpected error retrieving first level configuration: %(error)s",
            {"error": e},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving "
            / "the first level configuration.",
        ) from e


@router.get("/levels/{level_number}", response_model=LevelConfigurationResponse)
def get_level_configuration(
    level_number: int,
    env: Annotated[Environment, Depends(odoo_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)],
) -> LevelConfigurationResponse:
    try:
        LevelConfigModel = env["level.configuration"].sudo()
        export_data = LevelConfigModel.get_level_configuration_for_patient(
            level_number, partner.id
        )

        if not export_data.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=export_data.get(
                    "message",
                    "Failed to retrieve level configuration "
                    "due to an unknown error in Odoo method.",
                ),
            )

        response_timestamp = export_data.get("level_data", {}).get("timestamp")

        return LevelConfigurationResponse(
            success=export_data["success"],
            level_data=export_data["level_data"],
            timestamp=response_timestamp,
            message=export_data["message"],
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.args[0] if e.args else "Validation Error"),
        ) from e
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(
            "Unexpected error retrieving level %(level_number)s "
            " for partner %(partner_id)s: %(error)s",
            {
                "level_number": level_number,
                "partner_id": partner.id,
                "error": e,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An unexpected error occurred while retrieving "
                f"configuration for level {level_number}."
            ),
        ) from e
