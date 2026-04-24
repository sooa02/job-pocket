"""
repository/base.py

Repository 계층에서 공통으로 사용하는 테이블 네이밍 유틸입니다.

역할:
- TABLE_PREFIX를 기반으로 실제 테이블 이름을 생성합니다.

설계:
- 운영 환경에서는 TABLE_PREFIX="" (기본 테이블 사용)
- 테스트 환경에서는 TABLE_PREFIX="test_" (테스트 테이블 사용)

주의:
- repository 내부에서만 사용해야 합니다.
- SQL에서 테이블 이름을 직접 하드코딩하지 않고 반드시 이 함수를 사용합니다.
"""

TABLE_PREFIX: str = ""


def table_name(name: str) -> str:
    """
    테이블 이름에 prefix를 적용합니다.

    Args:
        name (str): 기본 테이블 이름 (예: "users")

    Returns:
        str: prefix가 적용된 실제 테이블 이름
             (예: "users", "test_users")
    """
    return f"{TABLE_PREFIX}{name}"
