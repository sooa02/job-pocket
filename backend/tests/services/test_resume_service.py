"""
test_resume_service.py

resume_service 계층의 이력서 조회/수정 비즈니스 로직을 검증합니다.
"""

import pytest
from fastapi import HTTPException

import services.resume_service as resume_service
from schemas import ResumeResponse, ResumeUpdateResponse


pytestmark = [pytest.mark.service, pytest.mark.unit]


def test_get_resume_data_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    사용자가 존재하면 이력서 데이터를 반환하는지 검증합니다.
    """
    fake_user: dict[str, str] = {
        "username": "홍길동",
        "password": "hashed-password",
        "email": "test@test.com",
        "resume_data": '{"personal": {"gender": "남성"}}',
    }

    def fake_get_user(email: str) -> dict[str, str]:
        return fake_user

    monkeypatch.setattr(resume_service, "get_user", fake_get_user)

    result: ResumeResponse = resume_service.get_resume_data("test@test.com")

    assert isinstance(result, ResumeResponse)
    assert result.resume_data == '{"personal": {"gender": "남성"}}'


def test_get_resume_data_returns_empty_json_when_resume_data_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    resume_data가 비어 있으면 기본 빈 JSON 문자열을 반환하는지 검증합니다.
    """
    fake_user: dict[str, str | None] = {
        "username": "홍길동",
        "password": "hashed-password",
        "email": "test@test.com",
        "resume_data": None,
    }

    def fake_get_user(email: str) -> dict[str, str | None]:
        return fake_user

    monkeypatch.setattr(resume_service, "get_user", fake_get_user)

    result: ResumeResponse = resume_service.get_resume_data("test@test.com")

    assert result.resume_data == "{}"


def test_get_resume_data_fail_user_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    사용자가 없으면 404 HTTPException을 발생시키는지 검증합니다.
    """

    def fake_get_user(email: str) -> None:
        return None

    monkeypatch.setattr(resume_service, "get_user", fake_get_user)

    with pytest.raises(HTTPException) as exc_info:
        resume_service.get_resume_data("missing@test.com")

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "유저를 찾을 수 없습니다."


def test_update_user_resume_data_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    이력서 데이터 수정이 성공하면 success 응답을 반환하는지 검증합니다.
    """

    def fake_update_resume_data(email: str, resume_data: dict) -> bool:
        return True

    monkeypatch.setattr(
        resume_service,
        "update_resume_data",
        fake_update_resume_data,
    )

    resume_data = {
        "personal": {"eng_name": "Gil Dong", "gender": "남성"},
        "education": {"school": "테스트대학교", "major": "컴퓨터공학"},
        "additional": {
            "internship": "백엔드 인턴",
            "awards": "해커톤 수상",
            "tech_stack": "Python, FastAPI, MySQL",
        },
    }

    result: ResumeUpdateResponse = resume_service.update_user_resume_data(
        email="test@test.com",
        resume_data=resume_data,
    )

    assert isinstance(result, ResumeUpdateResponse)
    assert result.status == "success"


def test_update_user_resume_data_fail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    이력서 데이터 수정이 실패하면 400 HTTPException을 발생시키는지 검증합니다.
    """

    def fake_update_resume_data(email: str, resume_data: dict) -> bool:
        return False

    monkeypatch.setattr(
        resume_service,
        "update_resume_data",
        fake_update_resume_data,
    )

    resume_data = {
        "personal": {"eng_name": "Gil Dong", "gender": "남성"},
        "education": {"school": "테스트대학교", "major": "컴퓨터공학"},
        "additional": {
            "internship": "백엔드 인턴",
            "awards": "해커톤 수상",
            "tech_stack": "Python, FastAPI, MySQL",
        },
    }

    with pytest.raises(HTTPException) as exc_info:
        resume_service.update_user_resume_data(
            email="missing@test.com",
            resume_data=resume_data,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "스펙 저장 실패"