from typing import List, Optional
from pydantic import BaseModel

class AngleRequirementSchema(BaseModel):
    angle: str
    min_angle: float
    max_angle: float
    description: Optional[str] = ""

class PoseDefinitionSchema(BaseModel):
    id: int
    name: str
    description: str
    require_feet_on_ground: bool
    foot_tolerance_y: float
    active: bool
    angle_requirements: List[AngleRequirementSchema]

class PosesExportResponse(BaseModel):
    success: bool
    poses: Optional[List[PoseDefinitionSchema]] = None
    pose: Optional[PoseDefinitionSchema] = None
    total_poses: Optional[int] = None
    timestamp: str
    message: str
