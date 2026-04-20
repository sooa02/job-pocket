from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Health check response schema.
    """

    status: str = Field(..., description="서비스 상태 (ok / degraded / error)")
    service: str = Field(..., description="서비스명 (job-pocket-backend)")
    version: str = Field(default="v.1.0", description="API 버전")
    message: str = Field(..., description="상태 상세 메시지")
