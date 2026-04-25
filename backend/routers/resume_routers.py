"""
resume_routers.py

이력서 조회/수정 API router입니다.
"""

from fastapi import APIRouter

from schemas import (
    ResumeResponse,
    ResumeUpdateRequest,
    ResumeUpdateResponse,
)
from services.resume_service import (
    get_resume_data,
    update_user_resume_data,
)

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.get("/{email}", response_model=ResumeResponse)
def get_resume(email: str) -> ResumeResponse:
    """
    사용자 이메일 기준으로 이력서 데이터를 조회합니다.
    """
    return get_resume_data(email)


@router.put("/{email}", response_model=ResumeUpdateResponse)
def update_resume(
    email: str,
    resume_data: ResumeUpdateRequest,
) -> ResumeUpdateResponse:
    """
    사용자 이메일 기준으로 이력서 데이터를 수정합니다.
    """
    return update_user_resume_data(
        email=email,
        resume_data=resume_data.model_dump(),
    )
