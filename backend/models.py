from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    annotator = "annotator"
    reviewer = "reviewer"
    admin = "admin"


class TaskStatus(str, Enum):
    pending = "pending"
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    arbitration = "arbitration"


class AnnotationType(str, Enum):
    bbox = "bbox"
    polygon = "polygon"
    mask = "mask"
    classification = "classification"


# User schemas
class UserCreate(BaseModel):
    username: str
    role: UserRole = UserRole.annotator


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: str


# Image schemas
class ImageCreate(BaseModel):
    filename: str
    filepath: str
    width: int
    height: int
    uncertainty_score: float = 0.5
    is_key_image: bool = False
    metadata_json: str = "{}"


class ImageResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    width: int
    height: int
    uncertainty_score: float
    is_key_image: bool
    metadata_json: str
    created_at: str


class UncertaintyUpdate(BaseModel):
    uncertainty_score: float


# Task schemas
class TaskResponse(BaseModel):
    id: int
    image_id: int
    assignee_id: Optional[int]
    status: str
    priority: float
    redundancy_group: Optional[str]
    assigned_at: Optional[str]
    completed_at: Optional[str]
    created_at: str


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class BulkTaskCreate(BaseModel):
    image_ids: List[int]
    redundancy: int = 3


class TaskAssignRequest(BaseModel):
    user_id: int


# Annotation schemas
class AnnotationCreate(BaseModel):
    task_id: int
    image_id: int
    user_id: int
    annotation_type: AnnotationType
    label: str
    data_json: str
    layer_index: int = 0


class AnnotationUpdate(BaseModel):
    label: Optional[str] = None
    data_json: Optional[str] = None
    layer_index: Optional[int] = None


class AnnotationResponse(BaseModel):
    id: int
    task_id: int
    image_id: int
    user_id: int
    annotation_type: str
    label: str
    data_json: str
    layer_index: int
    created_at: str
    updated_at: str


# QC schemas
class ConsistencyResult(BaseModel):
    id: int
    image_id: int
    annotation_id_a: int
    annotation_id_b: int
    metric_type: str
    score: float
    flagged: bool
    computed_at: str


class ArbitrationCreate(BaseModel):
    image_id: int
    consistency_result_id: int
    reviewer_id: int
    resolution_json: str


class ArbitrationResponse(BaseModel):
    id: int
    image_id: int
    consistency_result_id: Optional[int]
    reviewer_id: Optional[int]
    resolution_json: Optional[str]
    status: str
    created_at: str
    resolved_at: Optional[str]


# Stats schemas
class AnnotatorStats(BaseModel):
    user_id: int
    username: str
    total_tasks: int
    completed_tasks: int
    avg_consistency_score: Optional[float]
    gold_standard_deviation: Optional[float]


class OverviewStats(BaseModel):
    total_images: int
    total_tasks: int
    pending_tasks: int
    completed_tasks: int
    flagged_items: int
    total_annotators: int


# Kanban schemas
class KanbanResponse(BaseModel):
    pending: List[TaskResponse]
    assigned: List[TaskResponse]
    in_progress: List[TaskResponse]
    completed: List[TaskResponse]
    arbitration: List[TaskResponse]
