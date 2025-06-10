from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class AngleRequirementSchema(BaseModel):
    angle: str
    min_angle: float
    max_angle: float
    description: Optional[str] = ""

class PoseDefinitionSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    require_feet_on_ground: Optional[bool] = False
    foot_tolerance_y: Optional[float] = 0.0
    active: Optional[bool] = True
    angle_requirements: List[AngleRequirementSchema] = []

class MovementPosesSchema(BaseModel):
    forward: Optional[PoseDefinitionSchema] = None
    backward: Optional[PoseDefinitionSchema] = None
    left: Optional[PoseDefinitionSchema] = None
    right: Optional[PoseDefinitionSchema] = None

class TimingSchema(BaseModel):
    coin_challenge_time_limit: float

class LevelDataSchema(BaseModel):
    level_config_name: str
    level_number: int
    patient_id: Optional[int] = None
    patient_name: Optional[str] = None 
    movement_poses: MovementPosesSchema
    coin_poses: Dict[str, Optional[PoseDefinitionSchema]]
    timing: TimingSchema
    timestamp: str

class LevelConfigurationResponse(BaseModel):
    success: bool
    level_data: Optional[LevelDataSchema] = None
    timestamp: str
    message: str

class PosesExportResponse(BaseModel):
    success: bool
    poses: Optional[List[PoseDefinitionSchema]] = None
    pose: Optional[PoseDefinitionSchema] = None
    total_poses: Optional[int] = None
    timestamp: str
    message: str
