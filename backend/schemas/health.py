from pydantic import BaseModel, Field
from typing import Optional


class HealthResponse(BaseModel):
    """
    Health check response schema.
    """

    status: str = Field(..., description="서비스 상태 (ok / degraded / error)")
    service: str = Field(..., description="서비스명 (job-pocket-backend)")
    version: str = Field(default="v.1.0", description="API 버전")
    message: str = Field(..., description="상태 상세 메시지")


class DatabaseHealthItem(BaseModel):
    name: str
    status: str
    database: str
    user: str
    current_user: str
    detail: Optional[str] = None


class DatabaseHealthResponse(BaseModel):
    status: str
    rdb: DatabaseHealthItem
    vector: DatabaseHealthItem
