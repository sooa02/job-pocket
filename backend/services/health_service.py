from common.db import MYSQL_RDB_USER, MYSQL_VECTOR_USER, rdb_engine, vector_engine

from schemas.health import (
    HealthResponse,
    DatabaseHealthItem,
    DatabaseHealthResponse,
)

from utils.db_checker import check_database


def get_health_status() -> HealthResponse:
    """
    pipeline 컨테이너의 상태를 확인하기 위한 서비스 함수
    이 함수를 호출하면 컨테이너가 정상적으로 작동 중인지 확인할 수 있는 메시지를 반환

    :return HealthResponse: health status response containing status, service name, and detailed message
    """
    return HealthResponse(
        status="healthy API",
        service="job-pocket",
        version="0.1.0",
        message="서버가 정상적으로 동작 중 입니다.",
    )


def get_database_health() -> DatabaseHealthResponse:
    rdb_result = check_database(
        engine=rdb_engine,
        label="rdb",
        user=MYSQL_RDB_USER,
    )
    vector_result = check_database(
        engine=vector_engine,
        label="vector",
        user=MYSQL_VECTOR_USER,
    )

    overall_status = "ok"
    if rdb_result["status"] != "ok" or vector_result["status"] != "ok":
        overall_status = "degraded"

    return DatabaseHealthResponse(
        status=overall_status,
        rdb=DatabaseHealthItem(**rdb_result),
        vector=DatabaseHealthItem(**vector_result),
    )
