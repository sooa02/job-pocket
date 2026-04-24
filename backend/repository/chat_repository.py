"""
chat_repository

chat_history 테이블에 대한 DB 접근 로직을 담당합니다.

역할:
- 채팅 메시지 저장
- 사용자별 채팅 기록 조회
- 사용자별 채팅 기록 삭제

주의:
- 이 모듈은 DB 접근만 담당합니다.
- 비즈니스 로직은 services 계층에서 처리합니다.
"""

from typing import List

from pymysql.cursors import DictCursor

from common.db import rdb_engine
from schemas import ChatMessage


def save_chat_message(email: str, role: str, content: str) -> None:
    """
    사용자 채팅 메시지를 저장합니다.

    Args:
        email: 사용자 이메일.
        role: 메시지 역할. 예: "user", "assistant", "system".
        content: 메시지 본문.

    Returns:
        None
    """
    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            sql = """
                INSERT INTO chat_history (user_email, role, content)
                VALUES (%s, %s, %s)
            """
            c.execute(sql, (email, role, content))
            raw_conn.commit()
    finally:
        raw_conn.close()


def load_chat_history(email: str) -> List[ChatMessage]:
    """
    사용자 이메일을 기준으로 채팅 기록을 조회합니다.

    Args:
        email: 조회할 사용자 이메일.

    Returns:
        created_at 기준 오름차순으로 정렬된 채팅 메시지 목록.
        각 항목은 {"role": str, "content": str} 형태입니다.
    """
    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            sql = """
                SELECT role, content
                FROM chat_history
                WHERE user_email = %s
                ORDER BY created_at ASC
            """
            c.execute(sql, (email,))
            rows: List[ChatMessage] = c.fetchall()
            return rows
    finally:
        raw_conn.close()


def delete_chat_history(email: str) -> None:
    """
    사용자 이메일을 기준으로 채팅 기록을 삭제합니다.

    Args:
        email: 삭제할 채팅 기록의 사용자 이메일.

    Returns:
        None
    """
    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            sql = """
                DELETE FROM chat_history
                WHERE user_email = %s
            """
            c.execute(sql, (email,))
            raw_conn.commit()
    finally:
        raw_conn.close()
