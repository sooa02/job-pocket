"""
resume_service.py

이력서 정보 조회/수정 비즈니스 로직을 담당합니다.
"""

from fastapi import HTTPException

from repository import get_user, update_resume_data
from schemas import (
    ResumeData,
    ResumeResponse,
    ResumeUpdateResponse,
)


def get_resume_data(email: str) -> ResumeResponse:
    """
    사용자 이메일 기준으로 이력서 데이터를 조회합니다.
    """
    user = get_user(email)

    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    return ResumeResponse(
        resume_data=user["resume_data"] or "{}",
    )


def update_user_resume_data(
    email: str,
    resume_data: ResumeData,
) -> ResumeUpdateResponse:
    """
    사용자 이메일 기준으로 이력서 데이터를 수정합니다.
    """
    success: bool = update_resume_data(email, resume_data)

    if not success:
        raise HTTPException(status_code=400, detail="스펙 저장 실패")

    return ResumeUpdateResponse(status="success")
