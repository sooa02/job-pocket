"""
resume_schemas.py

이력서 관련 schema를 정의합니다.

TypedDict는 내부 로직(repository, service)에서 사용하고,
BaseModel은 API 요청/응답 검증에 사용합니다.
"""

from typing import Optional, TypedDict

from pydantic import BaseModel, Field


class Personal(TypedDict):
    """
    개인 기본 정보 구조입니다.
    """

    eng_name: str
    gender: str


class Education(TypedDict):
    """
    학력 정보 구조입니다.
    """

    school: str
    major: str


class Additional(TypedDict):
    """
    추가 이력 정보 구조입니다.
    """

    internship: str
    awards: str
    tech_stack: str


class ResumeData(TypedDict):
    """
    users.resume_data 컬럼에 저장되는 JSON 구조입니다.
    """

    personal: Personal
    education: Education
    additional: Additional


class PersonalReq(BaseModel):
    """
    이력서 수정 요청의 개인 기본 정보 schema입니다.
    """

    eng_name: str = Field(..., description="영문 이름")
    gender: str = Field(..., description="성별")


class EducationReq(BaseModel):
    """
    이력서 수정 요청의 학력 정보 schema입니다.
    """

    school: str = Field(..., description="학교명")
    major: str = Field(..., description="전공")


class AdditionalReq(BaseModel):
    """
    이력서 수정 요청의 추가 이력 정보 schema입니다.
    """

    internship: str = Field(..., description="인턴/경험")
    awards: str = Field(..., description="수상 이력")
    tech_stack: str = Field(..., description="기술 스택")


class ResumeUpdateRequest(BaseModel):
    """
    이력서 수정 API 요청 schema입니다.
    """

    personal: PersonalReq
    education: EducationReq
    additional: AdditionalReq


class PersonalPatchReq(BaseModel):
    """
    개인 기본 정보 부분 수정 요청 schema입니다.
    """

    eng_name: Optional[str] = Field(default=None, description="영문 이름")
    gender: Optional[str] = Field(default=None, description="성별")


class EducationPatchReq(BaseModel):
    """
    학력 정보 부분 수정 요청 schema입니다.
    """

    school: Optional[str] = Field(default=None, description="학교명")
    major: Optional[str] = Field(default=None, description="전공")


class AdditionalPatchReq(BaseModel):
    """
    추가 이력 정보 부분 수정 요청 schema입니다.
    """

    internship: Optional[str] = Field(default=None, description="인턴/경험")
    awards: Optional[str] = Field(default=None, description="수상 이력")
    tech_stack: Optional[str] = Field(default=None, description="기술 스택")


class ResumePatchRequest(BaseModel):
    """
    이력서 부분 수정 API 요청 schema입니다.
    """

    personal: Optional[PersonalPatchReq] = None
    education: Optional[EducationPatchReq] = None
    additional: Optional[AdditionalPatchReq] = None


class ResumeResponse(BaseModel):
    """
    이력서 조회 API 응답 schema입니다.
    """

    resume_data: str


class ResumeUpdateResponse(BaseModel):
    """
    이력서 수정 API 응답 schema입니다.
    """

    status: str


class ResumeErrorResponse(BaseModel):
    """
    이력서 API 에러 응답 schema입니다.
    """

    detail: str
