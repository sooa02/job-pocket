"""
repository/user_repository.py

users 테이블에 대한 DB 접근 레이어입니다.

역할:
- 이메일 기준 사용자 조회
- 웹 회원가입 사용자 생성
- 사용자 이력서 데이터 수정

주의:
- 비밀번호 해싱은 외부 계층에서 처리합니다.
- 비즈니스 로직은 포함하지 않습니다.
"""

import json
from typing import Optional, Tuple

from pymysql.cursors import DictCursor

from common.db import rdb_engine
from .base import table_name
from schemas import ResumeData, UserRow


def get_user(email: str) -> Optional[UserRow]:
    """
    이메일로 사용자 정보를 조회합니다.

    Args:
        email: 사용자 이메일

    Returns:
        사용자 정보 또는 None
    """
    users_table: str = table_name("users")

    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            sql: str = f"""
                SELECT username, password, email, resume_data
                FROM `{users_table}`
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
    resume_data: Optional[ResumeData] = None,
) -> Tuple[bool, str]:
    """
    웹 회원가입으로 사용자를 생성합니다.

    Args:
        name: 사용자 이름
        password_hash: 해싱된 비밀번호
        email: 사용자 이메일
        resume_data: 이력서 데이터

    Returns:
        성공 여부와 메시지
    """
    users_table: str = table_name("users")

    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            c.execute(
                f"SELECT email FROM `{users_table}` WHERE email = %s",
                (email,),
            )
            if c.fetchone():
                return False, "이미 가입된 이메일입니다."

            resume_json_str: str = (
                json.dumps(resume_data, ensure_ascii=False) if resume_data else "{}"
            )

            sql: str = f"""
                INSERT INTO `{users_table}` (username, password, email, resume_data)
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
    사용자의 이력서 데이터를 업데이트합니다.

    Args:
        email: 사용자 이메일
        resume_data: 이력서 데이터

    Returns:
        업데이트 성공 여부
    """
    users_table: str = table_name("users")

    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            resume_json_str: str = json.dumps(resume_data, ensure_ascii=False)

            sql: str = f"""
                UPDATE `{users_table}`
                SET resume_data = %s
                WHERE email = %s
            """
            c.execute(sql, (resume_json_str, email))

            success: bool = c.rowcount > 0
            raw_conn.commit()

            return success

    except Exception:
        raw_conn.rollback()
        raise

    finally:
        raw_conn.close()
