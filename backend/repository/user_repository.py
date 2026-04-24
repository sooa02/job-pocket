import json
from typing import Dict, Tuple

from pymysql.cursors import DictCursor

from common.db import rdb_engine
from schemas import ResumeData

UserTuple = Tuple[str, str, str, str]


def get_user(email: str) -> UserTuple | None:
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
            user = c.fetchone()

            if not user:
                return None

            return (
                user["username"],
                user["password"],
                user["email"],
                user["resume_data"],
            )
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


def update_password(email: str, new_password_hash: str) -> bool:
    """
    사용자 비밀번호를 변경합니다.

    Args:
        email: 비밀번호를 변경할 사용자 이메일.
        new_password_hash: 새로 해싱된 비밀번호.

    Returns:
        변경된 row가 있으면 True, 없으면 False를 반환합니다.
    """
    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            sql = """
                UPDATE users
                SET password = %s
                WHERE email = %s
            """
            c.execute(sql, (new_password_hash, email))
            success = c.rowcount > 0
            raw_conn.commit()

            return success

    except Exception:
        raw_conn.rollback()
        raise

    finally:
        raw_conn.close()


def update_resume_data(
    email: str,
    resume_data: Dict[str, Any],
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
