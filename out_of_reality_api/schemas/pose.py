from pydantic import BaseModel


class AngleRequirementSchema(BaseModel):
    angle: str
    min_angle: float
    max_angle: float
    description: str | None = ""


class PoseDefinitionSchema(BaseModel):
    id: int
    name: str
    description: str
    require_feet_on_ground: bool
    foot_tolerance_y: float
    active: bool
    angle_requirements: list[AngleRequirementSchema]


class PosesExportResponse(BaseModel):
    success: bool
    poses: list[PoseDefinitionSchema] | None = None
    pose: PoseDefinitionSchema | None = None
    total_poses: int | None = None
    timestamp: str
    message: str
