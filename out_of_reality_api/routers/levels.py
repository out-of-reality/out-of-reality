from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from odoo.api import Environment
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import authenticated_partner, odoo_env
from odoo.exceptions import ValidationError
from odoo.fields import Datetime # Added for fallback timestamp

from ..schemas import LevelConfigurationResponse

router = APIRouter(tags=["levels"])

@router.get("/levels/first_active", response_model=LevelConfigurationResponse)
def get_first_active_level_configuration(
    env: Annotated[Environment, Depends(odoo_env)],
) -> LevelConfigurationResponse:
    try:
        LevelConfigModel = env["level.configuration"].sudo()
        export_data = LevelConfigModel.get_first_lc_active()

        if not export_data.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=export_data.get("message", "No active level configuration found."),
            )

        response_timestamp = export_data.get("level_data", {}).get("timestamp")
        if not response_timestamp:
            response_timestamp = Datetime.now().isoformat()

        return LevelConfigurationResponse(
            success=export_data["success"],
            level_data=export_data["level_data"],
            timestamp=response_timestamp,
            message=export_data["message"],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while retrieving the first active level configuration.",
        )


@router.get("/levels/{level_number}", response_model=LevelConfigurationResponse)
def get_level_configuration(
    level_number: int,
    env: Annotated[Environment, Depends(odoo_env)],
    partner: Annotated[Partner, Depends(authenticated_partner)]
) -> LevelConfigurationResponse:
    """Get level configuration for current authenticated patient"""
    try:
        LevelConfigModel = env["level.configuration"].sudo()
        export_data = LevelConfigModel.get_level_configuration_for_patient(level_number, partner.id)

        if not export_data.get("success"):
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=export_data.get("message", "Failed to retrieve level configuration due to an unknown error in Odoo method."),
            )

        response_timestamp = export_data.get("level_data", {}).get("timestamp")
        if not response_timestamp:
            response_timestamp = Datetime.now().isoformat()

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
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error retrieving level {level_number} for partner {partner.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while retrieving configuration for level {level_number}.",
        )
