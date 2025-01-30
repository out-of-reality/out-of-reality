from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env

from ..schemas import PosesExportResponse

router = APIRouter(tags=["poses"])


@router.get("/poses/export", response_model=PosesExportResponse)
def export(env: Annotated[Environment, Depends(odoo_env)]) -> PosesExportResponse:
    """Export all active pose definitions to Unity"""
    try:
        PoseDefinition = env["pose.definition"].sudo()
        export_data = PoseDefinition.export_all_poses_for_unity()

        return PosesExportResponse(
            success=True,
            poses=export_data["poses"],
            total_poses=export_data["total_poses"],
            timestamp=export_data["timestamp"],
            message=f"Successfully exported {export_data['total_poses']} poses",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting poses: {str(e)}",
        ) from e
