"""
exaone_schemas.py - EXAONE 요청/응답 타입 정의
"""

from typing import Literal, TypedDict


class ChatMessage(TypedDict):
    """채팅 메시지."""

    role: Literal["system", "user", "assistant"]
    content: str


class ExaoneRequestInput(TypedDict, total=False):
    """EXAONE 추론 입력."""

    messages: list[ChatMessage]
    temperature: float
    max_new_tokens: int


class ExaoneRequest(TypedDict):
    """EXAONE 추론 요청."""

    input: ExaoneRequestInput


class ExaoneResponse(TypedDict, total=False):
    """EXAONE 추론 응답."""

    ok: bool
    text: str
    error: str
