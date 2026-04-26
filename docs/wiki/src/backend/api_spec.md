# 📡 Job-Pocket API 명세

> **문서 목적**: Job-Pocket 백엔드 FastAPI가 제공하는 모든 HTTP 엔드포인트의 Request/Response 스펙을 기술한다.  
> **최종 수정일**: 2026-04-26  
> **버전**: v0.3.0 (Pydantic 스키마 및 모듈화 라우터 반영)

---

## 1. 개요

모든 엔드포인트는 JSON 형식의 데이터를 주고받으며, FastAPI의 `APIRouter`를 통해 기능별로 분리되어 있습니다.

### 1.1 라우터 모듈 구성
- `/health` (`health_routers.py`)
- `/api/auth` (`auth_routers.py`)
- `/api/resume` (`resume_routers.py`)
- `/api/chat` (`chat_routers.py`)

---

## 2. Chat — RAG 파이프라인 (`/api/chat`)

자소서 생성 파이프라인은 프론트엔드가 상태(`ParsedUserRequest`)를 유지하며 각 단계를 순차적으로 호출하는 구조입니다.

### 2.1 `POST /step-parse`
사용자 입력을 LLM으로 파싱하여 구조화합니다.

**Request** (`StepParseRequest`)
```json
{
  "prompt": "네이버 백엔드 지원동기 500자",
  "model": "GPT-4o-mini"
}
```

**Response** (`ParsedUserRequest` 기반 JSON)
```json
{
  "raw_message": "네이버 백엔드 지원동기 500자",
  "company": "네이버",
  "job": "백엔드",
  "question": "지원동기",
  "char_limit": 500,
  "question_type": "motivation"
}
```

### 2.2 `POST /step-draft`
RAG 검색과 EXAONE 모델을 통해 초안을 생성합니다.

**Request** (`StepDraftRequest`)
```json
{
  "parsed_data": { /* step-parse 응답 데이터 */ },
  "user_info": ["홍길동", "hash", "email", "resume_data_str"],
  "model": "GPT-4o-mini"
}
```

**Response**
```json
{
  "draft": "(생성된 자소서 초안 본문)"
}
```

### 2.3 `POST /step-revise`
기존 생성된 초안에 대해 추가 수정을 지시합니다. (Draft 단계 대체)

**Request** (`StepReviseRequest`)
```json
{
  "existing_draft": "(이전 결과 본문)",
  "revision_request": "첫 문장을 더 담백하게",
  "model": "GPT-4o-mini"
}
```
**Response**: `{"revised": "수정된 본문"}`

### 2.4 `POST /step-refine`
초안의 논리적 흐름과 톤을 다듬습니다.

**Request** (`StepRefineRequest`)
```json
{
  "draft": "(초안 본문)",
  "parsed_data": { /* 파싱 데이터 */ },
  "model": "GPT-4o-mini"
}
```
**Response**: `{"refined": "다듬어진 본문"}`

### 2.5 `POST /step-fit`
요구된 글자 수(`char_limit`)에 맞춰 길이를 압축하거나 늘립니다.

**Request** (`StepFitRequest`)
```json
{
  "refined": "(다듬어진 본문)",
  "parsed_data": { /* 파싱 데이터 */ },
  "model": "GPT-4o-mini"
}
```
**Response**: `{"adjusted": "글자 수가 조정된 본문"}`

### 2.6 `POST /step-final`
평가를 생성하고 최종 마크다운 형태의 응답을 조립합니다.

**Request** (`StepFinalRequest`)
```json
{
  "adjusted": "(최종 본문)",
  "parsed_data": { /* 파싱 데이터 */ },
  "model": "GPT-4o-mini",
  "result_label": "자소서 초안",
  "change_summary": "요청사항 반영 요약"
}
```
**Response**
```json
{
  "final_response": "[자소서 초안]\n\n...본문...\n\n[평가 및 코멘트]\n평가 결과: 좋다\n이유: ..."
}
```

---

## 3. 이력 관리 및 기타 API

- **`POST /api/chat/message`**: 1건의 메시지 DB 저장 (role: user/assistant)
- **`GET /api/chat/history/{email}`**: 사용자의 과거 대화 내역 전체 로드
- **`DELETE /api/chat/history/{email}`**: 대화 내역 초기화
- **`PUT /api/resume/{email}`**: 이력(JSON) 덮어쓰기 업데이트
- **`POST /api/auth/login`**: 사용자 인증 및 정보 조회

*(모든 API는 `backend/schemas/` 내의 Pydantic 모델로 강한 타입 검증을 받습니다.)*

---

*last updated: 2026-04-26 | 조라에몽 팀*