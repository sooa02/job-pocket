"""
repository package

데이터베이스 접근 계층(Repository Layer)의 공개 인터페이스를 정의합니다.

역할:
- users, chat_history 등 DB 테이블에 대한 CRUD 기능 제공
- service 계층에서 사용할 함수들을 export

구성:
- user_repository: 사용자 관련 DB 로직
- chat_repository: 채팅 기록 관련 DB 로직

주의:
- 이 패키지는 DB 접근만 담당합니다.
- 비즈니스 로직은 services 계층에서 처리해야 합니다.
"""

# user repository
from .user_repository import (
    get_user,
    add_user_via_web,
    update_resume_data,
)

# chat repository
from .chat_repository import (
    save_chat_message,
    load_chat_history,
    delete_chat_history,
)

__all__ = [
    # user
    "get_user",
    "add_user_via_web",
    "update_resume_data",
    # chat
    "save_chat_message",
    "load_chat_history",
    "delete_chat_history",
]
