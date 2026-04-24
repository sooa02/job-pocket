"""
repository/chat_repository.py

chat_history 테이블에 대한 DB 접근 레이어입니다.

역할:
- 채팅 메시지 저장
- 사용자별 채팅 기록 조회
- 사용자별 채팅 기록 삭제

설계:
- TABLE_PREFIX를 통해 테스트/운영 테이블을 분리합니다.
- 테스트 환경에서는 test_chat_history를 사용합니다.

주의:
- 이 모듈은 DB 접근만 담당합니다.
- 비즈니스 로직은 포함하지 않습니다.
"""

from typing import List

from pymysql.cursors import DictCursor

from common.db import rdb_engine
from .base import table_name
from schemas import ChatMessage


def save_chat_message(email: str, role: str, content: str) -> None:
    """
    사용자 채팅 메시지를 저장합니다.

    Args:
        email: 사용자 이메일
        role: 메시지 역할 (user, assistant 등)
        content: 메시지 내용
    """
    chat_table: str = table_name("chat_history")

    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            sql: str = f"""
                INSERT INTO `{chat_table}` (user_email, role, content)
                VALUES (%s, %s, %s)
            """
            c.execute(sql, (email, role, content))
            raw_conn.commit()
    finally:
        raw_conn.close()


def load_chat_history(email: str) -> List[ChatMessage]:
    """
    사용자 채팅 기록을 조회합니다.

    Args:
        email: 사용자 이메일

    Returns:
        채팅 메시지 리스트 (시간순 정렬)
    """
    chat_table: str = table_name("chat_history")

    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            sql: str = f"""
                SELECT role, content
                FROM `{chat_table}`
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
    사용자 채팅 기록을 삭제합니다.

    Args:
        email: 사용자 이메일
    """
    chat_table: str = table_name("chat_history")

    raw_conn = rdb_engine.raw_connection()
    try:
        with raw_conn.cursor(DictCursor) as c:
            sql: str = f"""
                DELETE FROM `{chat_table}`
                WHERE user_email = %s
            """
            c.execute(sql, (email,))
            raw_conn.commit()
    finally:
        raw_conn.close()