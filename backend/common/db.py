"""
common/db.py

데이터베이스 엔진 생성 및 설정 모듈

이 모듈은 다음 역할을 담당한다:
- 필수 환경 변수 검증
- RDB / Vector DB용 SQLAlchemy Engine 생성 함수 제공
- 애플리케이션 실행 시 사용할 기본 Engine 객체 제공

설계 원칙:
- Engine은 함수(factory)로 생성하여 테스트 시 override 가능하도록 한다
- 환경 변수는 import 시점에 강제 검증한다
- 테스트 환경에서는 전역 engine이 아닌, 커스텀 db_url을 전달하여 사용한다

필수 환경 변수:
- RDB_URL: 관계형 DB(SQLAlchemy URL)
- VECTOR_DB_URL: 벡터 DB(SQLAlchemy URL)
- MYSQL_RDB_USER: RDB 사용자명
- MYSQL_VECTOR_USER: Vector DB 사용자명
"""

from os import getenv
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def _require_env(key: str) -> str:
    """
    필수 환경 변수를 가져온다.

    Args:
        key (str): 환경 변수 이름

    Returns:
        str: 환경 변수 값

    Raises:
        ValueError: 환경 변수가 없거나 비어있는 경우
    """
    value: Optional[str] = getenv(key)
    if value is None or value.strip() == "":
        raise ValueError(f"environment variable '{key}' is required")
    return value


RDB_URL: str = _require_env("RDB_URL")
VECTOR_DB_URL: str = _require_env("VECTOR_DB_URL")

MYSQL_RDB_USER: str = _require_env("MYSQL_RDB_USER")
MYSQL_VECTOR_USER: str = _require_env("MYSQL_VECTOR_USER")


def create_rdb_engine(db_url: Optional[str] = None) -> Engine:
    """
    RDB(MySQL)용 SQLAlchemy Engine을 생성한다.

    Args:
        db_url (Optional[str]):
            사용할 DB 연결 URL.
            None이면 기본 환경 변수 RDB_URL을 사용한다.
            (테스트 환경에서 override 용도로 사용)

    Returns:
        Engine: SQLAlchemy Engine 객체
    """
    return create_engine(
        db_url or RDB_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def create_vector_engine(db_url: Optional[str] = None) -> Engine:
    """
    Vector DB용 SQLAlchemy Engine을 생성한다.

    Args:
        db_url (Optional[str]):
            사용할 DB 연결 URL.
            None이면 기본 환경 변수 VECTOR_DB_URL을 사용한다.

    Returns:
        Engine: SQLAlchemy Engine 객체
    """
    return create_engine(
        db_url or VECTOR_DB_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


# 기본 엔진 (애플리케이션 실행 시 사용)
rdb_engine: Engine = create_rdb_engine()
vector_engine: Engine = create_vector_engine()
