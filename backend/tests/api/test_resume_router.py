"""
Resume API 테스트.

관련 테스트 케이스: TC-006 ~ TC-008
커버하는 엔드포인트:
- GET /resume/{email}
- PUT /resume/{email}
"""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient


pytestmark = [pytest.mark.router, pytest.mark.auth, pytest.mark.integration]


class TestGetResume:
    """이력서 조회 엔드포인트를 검증합니다."""

    def test_get_resume_success_TC006(
        self,
        client: TestClient,
        test_user: dict[str, str],
    ) -> None:
        """TC-006: 저장된 이력서 데이터를 정상 조회하는지 검증합니다."""
        payload: dict[str, Any] = {
            "personal": {
                "eng_name": "Hong",
                "gender": "남성",
            },
            "education": {
                "school": "○○대",
                "major": "컴퓨터공학",
            },
            "additional": {
                "internship": "ABC 인턴 3개월",
                "awards": "",
                "tech_stack": "Python",
            },
        }

        put_response = client.put(
            f"/resume/{test_user['email']}",
            json=payload,
        )
        assert put_response.status_code == 200

        response = client.get(f"/resume/{test_user['email']}")
        assert response.status_code == 200

        data: dict[str, Any] = response.json()
        assert "resume_data" in data

        resume_data: dict[str, Any] = json.loads(data["resume_data"])
        assert resume_data["personal"]["eng_name"] == "Hong"
        assert resume_data["personal"]["gender"] == "남성"
        assert resume_data["education"]["school"] == "○○대"
        assert resume_data["education"]["major"] == "컴퓨터공학"
        assert resume_data["additional"]["tech_stack"] == "Python"

    def test_get_resume_nonexistent_user_returns_404_TC008(
        self,
        client: TestClient,
        clean_db: Any,
    ) -> None:
        """TC-008: 존재하지 않는 유저의 이력서 조회 시 404 응답을 반환하는지 검증합니다."""
        response = client.get("/resume/ghost@example.com")

        assert response.status_code == 404
        assert "detail" in response.json()


class TestUpdateResume:
    """이력서 수정 엔드포인트를 검증합니다."""

    def test_update_resume_success_TC007(
        self,
        client: TestClient,
        test_user: dict[str, str],
    ) -> None:
        """TC-007: 이력서 데이터 수정이 정상 수행되는지 검증합니다."""
        payload: dict[str, Any] = {
            "personal": {
                "eng_name": "Kim",
                "gender": "여성",
            },
            "education": {
                "school": "△△대",
                "major": "통계학",
            },
            "additional": {
                "internship": "DEF 인턴",
                "awards": "장학금",
                "tech_stack": "R, Python, SQL",
            },
        }

        response = client.put(
            f"/resume/{test_user['email']}",
            json=payload,
        )

        assert response.status_code == 200

        data: dict[str, Any] = response.json()
        assert data["status"] == "success"

    def test_update_resume_overwrites_previous_data(
        self,
        client: TestClient,
        test_user: dict[str, str],
    ) -> None:
        """동일 이메일에 대해 PUT 요청 시 기존 이력서 데이터가 덮어써지는지 검증합니다."""
        first_payload: dict[str, Any] = {
            "personal": {
                "eng_name": "Hong",
                "gender": "남성",
            },
            "education": {
                "school": "A대",
                "major": "컴퓨터공학",
            },
            "additional": {
                "internship": "",
                "awards": "",
                "tech_stack": "Python",
            },
        }

        second_payload: dict[str, Any] = {
            "personal": {
                "eng_name": "Kim",
                "gender": "여성",
            },
            "education": {
                "school": "B대",
                "major": "통계학",
            },
            "additional": {
                "internship": "",
                "awards": "",
                "tech_stack": "Java",
            },
        }

        first_response = client.put(
            f"/resume/{test_user['email']}",
            json=first_payload,
        )
        assert first_response.status_code == 200

        second_response = client.put(
            f"/resume/{test_user['email']}",
            json=second_payload,
        )
        assert second_response.status_code == 200

        response = client.get(f"/resume/{test_user['email']}")
        assert response.status_code == 200

        data: dict[str, Any] = response.json()
        resume_data: dict[str, Any] = json.loads(data["resume_data"])

        assert resume_data["personal"]["eng_name"] == "Kim"
        assert resume_data["personal"]["gender"] == "여성"
        assert resume_data["education"]["school"] == "B대"
        assert resume_data["education"]["major"] == "통계학"
        assert resume_data["additional"]["tech_stack"] == "Java"

    def test_update_resume_invalid_empty_payload_returns_422(
        self,
        client: TestClient,
        test_user: dict[str, str],
    ) -> None:
        """필수 이력서 필드가 비어 있으면 422 응답을 반환하는지 검증합니다."""
        response = client.put(
            f"/resume/{test_user['email']}",
            json={
                "personal": {},
                "education": {},
                "additional": {},
            },
        )

        assert response.status_code == 422

    def test_update_resume_nonexistent_user_returns_400_or_404(
        self,
        client: TestClient,
        clean_db: Any,
    ) -> None:
        """존재하지 않는 유저의 이력서 수정 요청 시 400 또는 404 응답을 반환하는지 검증합니다."""
        response = client.put(
            "/resume/ghost@example.com",
            json={
                "personal": {
                    "eng_name": "Ghost",
                    "gender": "남성",
                },
                "education": {
                    "school": "없는대",
                    "major": "없음",
                },
                "additional": {
                    "internship": "",
                    "awards": "",
                    "tech_stack": "",
                },
            },
        )

        assert response.status_code in (400, 404)

    def test_update_resume_with_korean_content(
        self,
        client: TestClient,
        test_user: dict[str, str],
    ) -> None:
        """한글 및 이모지 콘텐츠가 정상 저장·조회되는지 검증합니다."""
        payload: dict[str, Any] = {
            "personal": {
                "eng_name": "Hong",
                "gender": "남성",
            },
            "education": {
                "school": "서울대학교",
                "major": "컴퓨터공학",
            },
            "additional": {
                "internship": "삼성전자 인턴 3개월 🎯",
                "awards": "대상",
                "tech_stack": "Python, SQL, 도커",
            },
        }

        put_response = client.put(
            f"/resume/{test_user['email']}",
            json=payload,
        )
        assert put_response.status_code == 200

        response = client.get(f"/resume/{test_user['email']}")
        assert response.status_code == 200

        data: dict[str, Any] = response.json()
        resume_data: dict[str, Any] = json.loads(data["resume_data"])

        assert resume_data["education"]["school"] == "서울대학교"
        assert resume_data["education"]["major"] == "컴퓨터공학"
        assert "🎯" in resume_data["additional"]["internship"]
