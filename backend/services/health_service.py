from schemas.health import HealthResponse


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
