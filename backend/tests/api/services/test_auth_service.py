"""
test_auth_service

auth_service 계층의 비즈니스 로직을 검증하는 단위 테스트 모듈입니다.
"""

import pytest
from fastapi import HTTPException

import services.auth_service as auth_service

pytestmark = [pytest.mark.service, pytest.mark.auth]


def test_login_user_success(monkeypatch):
    password = "test1234"
    hashed_password = auth_service.hash_pw(password)

    fake_user = {
        "username": "홍길동",
        "password": hashed_password,
        "email": "test@test.com",
        "resume_data": "{}",
    }

    monkeypatch.setattr(auth_service, "get_user", lambda email: fake_user)

    result = auth_service.login_user(
        email="test@test.com",
        password=password,
    )

    assert result["status"] == "success"
    assert result["user_info"]["username"] == "홍길동"
    assert result["user_info"]["email"] == "test@test.com"
    assert result["user_info"]["resume_data"] == "{}"
    assert "password" not in result["user_info"]


def test_login_user_fail_wrong_password(monkeypatch):
    fake_user = {
        "username": "홍길동",
        "password": auth_service.hash_pw("correct-password"),
        "email": "test@test.com",
        "resume_data": "{}",
    }

    monkeypatch.setattr(auth_service, "get_user", lambda email: fake_user)

    with pytest.raises(HTTPException) as exc_info:
        auth_service.login_user(
            email="test@test.com",
            password="wrong-password",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "이메일 또는 비밀번호가 일치하지 않습니다."


def test_login_user_fail_user_not_found(monkeypatch):
    monkeypatch.setattr(auth_service, "get_user", lambda email: None)

    with pytest.raises(HTTPException) as exc_info:
        auth_service.login_user(
            email="missing@test.com",
            password="test1234",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "이메일 또는 비밀번호가 일치하지 않습니다."


def test_signup_user_success(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "add_user_via_web",
        lambda name, password_hash, email: (True, "회원가입 성공"),
    )

    result = auth_service.signup_user(
        name="홍길동",
        email="test@test.com",
        password="test1234",
    )

    assert result["status"] == "success"
    assert result["detail"] == "회원가입 성공"


def test_signup_user_fail_duplicate_email(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "add_user_via_web",
        lambda name, password_hash, email: (False, "이미 가입된 이메일입니다."),
    )

    with pytest.raises(HTTPException) as exc_info:
        auth_service.signup_user(
            name="홍길동",
            email="test@test.com",
            password="test1234",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "이미 가입된 이메일입니다."


def test_signup_user_fail_repository_error(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "add_user_via_web",
        lambda name, password_hash, email: (False, "오류 발생: DB connection failed"),
    )

    with pytest.raises(HTTPException) as exc_info:
        auth_service.signup_user(
            name="홍길동",
            email="test@test.com",
            password="test1234",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "오류 발생: DB connection failed"


def test_login_user_fail_empty_password(monkeypatch):
    fake_user = {
        "username": "홍길동",
        "password": auth_service.hash_pw("correct-password"),
        "email": "test@test.com",
        "resume_data": "{}",
    }

    monkeypatch.setattr(auth_service, "get_user", lambda email: fake_user)

    with pytest.raises(HTTPException) as exc_info:
        auth_service.login_user(
            email="test@test.com",
            password="",
        )

    assert exc_info.value.status_code == 401
