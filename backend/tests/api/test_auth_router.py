"""
Authentication API 테스트.

관련 테스트 케이스: TC-001 ~ TC-004
커버하는 엔드포인트:
- POST /auth/signup
- POST /auth/login
"""

from typing import Any

import pytest
from fastapi.testclient import TestClient

from repository import get_user
from schemas import UserRow
from utils.security import hash_pw


pytestmark = [pytest.mark.router, pytest.mark.auth, pytest.mark.integration]


class TestSignup:
    """회원가입 엔드포인트를 검증합니다."""

    def test_signup_success(self, client: TestClient, clean_db: Any) -> None:
        """정상 회원가입 시 성공 응답과 DB 저장 여부를 검증합니다."""
        response = client.post(
            "/auth/signup",
            json={
                "name": "신규유저",
                "email": "newuser@example.com",
                "password": "pass123",
            },
        )

        assert response.status_code == 200

        data: dict[str, Any] = response.json()
        assert data["status"] == "success"
        assert "회원가입 성공" in data["detail"]

        user: UserRow | None = get_user("newuser@example.com")
        assert user is not None
        assert user["username"] == "신규유저"
        assert user["email"] == "newuser@example.com"

    def test_signup_password_is_hashed(
        self,
        client: TestClient,
        clean_db: Any,
    ) -> None:
        """회원가입 시 비밀번호가 해시되어 저장되는지 검증합니다."""
        plain_password: str = "pass123"

        response = client.post(
            "/auth/signup",
            json={
                "name": "해시테스트",
                "email": "hash@example.com",
                "password": plain_password,
            },
        )

        assert response.status_code == 200

        user: UserRow | None = get_user("hash@example.com")
        assert user is not None

        stored_password: str = user["password"]

        assert stored_password != plain_password
        assert len(stored_password) == 64
        assert stored_password == hash_pw(plain_password)

    def test_signup_duplicate_email_returns_400(
        self,
        client: TestClient,
        test_user: dict[str, str],
    ) -> None:
        """이미 가입된 이메일로 회원가입 시 400 응답을 반환하는지 검증합니다."""
        response = client.post(
            "/auth/signup",
            json={
                "name": "중복유저",
                "email": test_user["email"],
                "password": "anotherpass",
            },
        )

        assert response.status_code == 400
        assert "이미" in response.json()["detail"]

    @pytest.mark.parametrize(
        "invalid_payload",
        [
            {},
            {"email": "incomplete@example.com"},
            {"name": "a", "email": "not-email", "password": "pass123"},
        ],
    )
    def test_signup_invalid_payload_returns_422(
        self,
        client: TestClient,
        clean_db: Any,
        invalid_payload: dict[str, Any],
    ) -> None:
        """잘못된 회원가입 payload 요청 시 422 응답을 반환하는지 검증합니다."""
        response = client.post("/auth/signup", json=invalid_payload)

        assert response.status_code == 422


class TestLogin:
    """로그인 엔드포인트를 검증합니다."""

    def test_login_success(
        self,
        client: TestClient,
        test_user: dict[str, str],
    ) -> None:
        """정상 로그인 시 성공 응답과 사용자 정보를 반환하는지 검증합니다."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 200

        data: dict[str, Any] = response.json()
        assert data["status"] == "success"

        user_info: dict[str, Any] = data["user_info"]
        assert user_info["username"] == test_user["name"]
        assert user_info["email"] == test_user["email"]
        assert "password" not in user_info

    def test_login_wrong_password_returns_401(
        self,
        client: TestClient,
        test_user: dict[str, str],
    ) -> None:
        """잘못된 비밀번호로 로그인 시 401 응답을 반환하는지 검증합니다."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrong_password",
            },
        )

        assert response.status_code == 401
        assert "일치하지 않" in response.json()["detail"]

    def test_login_nonexistent_email_returns_401(
        self,
        client: TestClient,
        clean_db: Any,
    ) -> None:
        """존재하지 않는 이메일로 로그인 시 401 응답을 반환하는지 검증합니다."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "pass123",
            },
        )

        assert response.status_code == 401
