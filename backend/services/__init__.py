"""
services package

비즈니스 로직(Service Layer)을 외부에 노출하는 인터페이스 모듈입니다.

역할:
- router 계층에서 사용할 서비스 함수들을 export
- repository(DB 접근)와 router(API) 사이의 중간 계층 역할 수행

구성:
- health_service: 서버 및 DB 상태 체크 로직
- chat_ollama: RunPod 기반 LLM 호출 로직
- auth_service: 인증(로그인/회원가입) 비즈니스 로직

주의:
- 이 패키지는 비즈니스 로직만 담당합니다.
- DB 접근은 repository 계층에서 수행합니다.
- 외부 API 호출은 services 내부에서 처리합니다.
"""

# health services
from .health_service import get_health_status, get_database_health

# chat services
from .chat_ollama import call_runpod_ollama

# auth services
from .auth_service import login_user, signup_user

# resume services
from .resume_service import get_resume_data, update_resume_data, update_user_resume_data

__all__ = [
    # health
    "get_health_status",
    "get_database_health",
    # chat
    "call_runpod_ollama",
    # auth
    "login_user",
    "signup_user",
    # resume
    "get_resume_data",
    "update_resume_data",
    "update_user_resume_data",
]
