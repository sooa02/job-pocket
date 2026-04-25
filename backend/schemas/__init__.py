"""
schemas package

FastAPI 애플리케이션 전반에서 사용하는 데이터 구조(Type Schema)를 정의하고,
외부에서 사용할 수 있도록 export하는 모듈입니다.
"""

# health schemas
from .health_schemas import (
    DatabaseHealthResponse,
    DatabaseHealthItem,
    HealthResponse,
)

# auth schemas
from .auth_schemas import (
    SignupRequest,
    LoginRequest,
    AuthStatusResponse,
    LoginUserInfo,
    LoginResponse,
    SignupResponse,
)

# user schemas
from .user_schemas import (
    UserRow,
    UserWithResume,
)

# resume schemas
from .resume_schemas import (
    ResumeData,
    Personal,
    Education,
    Additional,
    ResumeResponse,
    ResumeUpdateResponse,
    ResumeUpdateRequest,
    ResumeErrorResponse,
)

# chat schemas
from .chat_schemas import (
    ChatMessage,
)


__all__ = [
    # health
    "HealthResponse",
    "DatabaseHealthItem",
    "DatabaseHealthResponse",
    # auth
    "SignupRequest",
    "LoginRequest",
    "AuthStatusResponse",
    "LoginUserInfo",
    "LoginResponse",
    "SignupResponse",
    # user
    "UserRow",
    "UserWithResume",
    # resume
    "ResumeData",
    "Personal",
    "Education",
    "Additional",
    "ResumeResponse",
    "ResumeUpdateResponse",
    "ResumeUpdateRequest",
    "ResumeErrorResponse",
    # chat
    "ChatMessage",
]
