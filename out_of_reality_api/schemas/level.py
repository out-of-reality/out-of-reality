from pydantic import BaseModel

from .pose import PoseDefinitionSchema


class MovementPosesSchema(BaseModel):
    forward: PoseDefinitionSchema | None = None
    backward: PoseDefinitionSchema | None = None
    left: PoseDefinitionSchema | None = None
    right: PoseDefinitionSchema | None = None


class TimingSchema(BaseModel):
    coin_challenge_time_limit: float


class LevelDataSchema(BaseModel):
    level_config_name: str
    level_number: int
    patient_id: int | None = None
    patient_name: str | None = None
    movement_poses: MovementPosesSchema
    coin_poses: dict[str, PoseDefinitionSchema | None]
    timing: TimingSchema
    timestamp: str


class LevelConfigurationResponse(BaseModel):
    success: bool
    level_data: LevelDataSchema | None = None
    timestamp: str
    message: str
