import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        raise ValueError(f"environment variable '{key}' is required")
    return value


RDB_URL = _require_env("RDB_URL")
VECTOR_DB_URL = _require_env("VECTOR_DB_URL")

MYSQL_RDB_USER = _require_env("MYSQL_RDB_USER")
MYSQL_VECTOR_USER = _require_env("MYSQL_VECTOR_USER")


def create_rdb_engine() -> Engine:
    return create_engine(
        RDB_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def create_vector_engine() -> Engine:
    return create_engine(
        VECTOR_DB_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


rdb_engine = create_rdb_engine()
vector_engine = create_vector_engine()
