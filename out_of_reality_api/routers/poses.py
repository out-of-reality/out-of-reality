from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime, timedelta
from typing import Annotated

from odoo.api import Environment
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import authenticated_partner, odoo_env
from odoo.addons.clinic_management.models.pose_definition import PoseDefinition
import traceback
from ..schemas import PoseDefinitionSchema, PosesExportResponse

router = APIRouter(tags=["poses"])


@router.get("/poses/export", response_model=PosesExportResponse)
def export(env: Annotated[Environment, Depends(odoo_env)]) -> PosesExportResponse:
    """Export all active pose definitions to Unity"""
    try:
        PoseDefinition = env["pose.definition"].sudo()
        export_data = PoseDefinition.export_all_poses_for_unity()

        return {
            "success": True,
            "poses": export_data["poses"],
            "total_poses": export_data["total_poses"],
            "timestamp": export_data["timestamp"],
            "message": f"Successfully exported {export_data['total_poses']} poses",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting poses: {str(e)}",
        )
# (env: Annotated[Environment, Depends(odoo_env)], partner: Annotated[Partner, Depends(authenticated_partner)])
