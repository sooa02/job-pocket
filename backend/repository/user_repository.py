"""
user_repository

users 테이블에 대한 DB 접근 로직을 담당합니다.

역할:
- 이메일 기준 사용자 조회
- 웹 회원가입 사용자 생성
- 사용자 이력서 데이터 수정

주의:
- 이 모듈은 DB 접근만 담당합니다.
- 비밀번호 해싱은 utils.security 또는 service 계층에서 처리합니다.
- 비즈니스 로직은 services 계층에서 처리합니다.
"""

import json
from typing import Tuple

from pymysql.cursors import DictCursor

from common.db import rdb_engine
from schemas import ResumeData, UserRow


def get_user(email: str) -> UserRow | None:
    """
    이메일을 기준으로 사용자 정보를 조회합니다.

    Args:
        email: 조회할 사용자 이메일.

    Returns:
        사용자가 존재하면 (username, password, email, resume_data) 튜플을 반환합니다.
        사용자가 없으면 None을 반환합니다.
    """
    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            sql = """
                SELECT username, password, email, resume_data
                FROM users
                WHERE email = %s
            """
            c.execute(sql, (email,))

            return c.fetchone()

    finally:
        raw_conn.close()


def add_user_via_web(
    name: str,
    password_hash: str,
    email: str,
    resume_data: ResumeData | None = None,
) -> Tuple[bool, str]:
    """
    웹 회원가입 요청으로 사용자를 생성합니다.

    Args:
        name: 사용자 이름.
        password_hash: 해싱된 비밀번호.
        email: 사용자 이메일.
        resume_data: 선택 입력 이력서 데이터.

    Returns:
        (성공 여부, 메시지) 튜플을 반환합니다.
    """
    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            c.execute("SELECT email FROM users WHERE email = %s", (email,))
            if c.fetchone():
                return False, "이미 가입된 이메일입니다."

            resume_json_str = (
                json.dumps(resume_data, ensure_ascii=False) if resume_data else "{}"
            )

            sql = """
                INSERT INTO users (username, password, email, resume_data)
                VALUES (%s, %s, %s, %s)
            """
            c.execute(sql, (name, password_hash, email, resume_json_str))
            raw_conn.commit()

            return True, "회원가입 성공"

    except Exception as e:
        raw_conn.rollback()
        return False, f"오류 발생: {e}"

    finally:
        raw_conn.close()


def update_resume_data(
    email: str,
    resume_data: ResumeData,
) -> bool:
    """
    사용자의 이력서 데이터를 JSON 문자열로 저장합니다.

    Args:
        email: 이력서 데이터를 변경할 사용자 이메일.
        resume_data: 저장할 이력서 데이터.

    Returns:
        변경된 row가 있으면 True, 없으면 False를 반환합니다.
    """
    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            resume_json_str = json.dumps(resume_data, ensure_ascii=False)

            sql = """
                UPDATE users
                SET resume_data = %s
                WHERE email = %s
            """
            c.execute(sql, (resume_json_str, email))

            success = c.rowcount > 0
            raw_conn.commit()

            return success

    except Exception:
        raw_conn.rollback()
        raise

    finally:
        raw_conn.close()
