# 🏗️ Job-Pocket 백엔드 아키텍처

> **문서 목적**: FastAPI 기반 백엔드의 계층 구조, 의존성 흐름, 설계 패턴, 주요 관심사 분리 전략을 기술한다.  
> **최종 수정일**: 2026-04-26  
> **버전**: v0.3.0  
> **관련 파일**: `backend/**/*.py`

---

## 1. 설계 원칙

### 1.1 계층 분리 (Layered Architecture)
백엔드는 HTTP 요청 처리, 비즈니스 로직, 데이터 영속성을 명확히 분리합니다. 
이를 위해 **Service-Repository 패턴**을 전면 도입했습니다. 
각 계층은 상위 계층에만 의존하며, 하위 계층은 상위 계층의 존재를 알지 못합니다. 

### 1.2 모듈화 (Modularization)
특히 RAG 텍스트 생성의 핵심 로직인 `chat` 도메인은 단일 거대 파일에서 벗어나 `parser`, `generator`, `evaluator`, `analyzer` 등의 서브 모듈로 책임이 세분화되었습니다.

### 1.3 Stateless Backend
FastAPI 프로세스는 상태를 유지하지 않습니다. 
대화 상태나 생성 중간 결과물은 프론트엔드(`st.session_state`)에서 관리되거나, 각 단계가 끝난 후 즉시 DB에 저장됩니다. 
단, LLM 클라이언트와 DB 엔진(SQLAlchemy)은 애플리케이션 시작 시 전역 싱글톤으로 초기화되어 재사용됩니다.

---

## 2. 디렉토리 구조

```text
backend/
├── main.py                    # FastAPI 앱 엔트리포인트
├── pytest.ini                 # 테스트 설정
├── common/                    # 전역 설정 및 유틸
│   ├── config.py              # 환경변수 로드
│   ├── db.py                  # SQLAlchemy Engine 생성
│   └── api_request.py
├── middlewares/               # CORS 등 미들웨어
├── repository/                # DB 데이터 액세스 계층
│   ├── chat_repository.py
│   ├── retrieval_repository.py
│   └── user_repository.py
├── routers/                   # HTTP 엔드포인트 계층
│   ├── auth_routers.py
│   ├── chat_routers.py
│   ├── health_routers.py
│   └── resume_routers.py
├── schemas/                   # Pydantic Req/Res 모델
│   ├── chat_schemas.py
│   └── ...
├── services/                  # 비즈니스 로직 (Orchestrator)
│   ├── chat_logic.py          # 파이프라인 조율
│   ├── retrieval_service.py   # FAISS 검색 수행
│   └── chat/                  # 단위 모듈 (생성, 평가 등)
│       ├── analyzer.py
│       ├── evaluator.py
│       ├── generator.py
│       ├── parser.py
│       └── run_exaone.py
└── tests/                     # 단위, 통합, 평가 테스트
```

---

## 3. 계층별 상세 역할

### 3.1 Routers (`routers/`)
- HTTP 통신의 진입점입니다.
- `schemas/`에 정의된 Pydantic 모델을 통해 요청 바디를 검증합니다.
- 비즈니스 로직은 작성하지 않으며, 검증된 데이터를 `services/` 계층의 함수로 전달하고 결과를 반환합니다.

### 3.2 Services (`services/`)
- 도메인 비즈니스 로직을 수행합니다.
- **Orchestrator (`chat_logic.py`)**: 4~5단계의 생성/수정 파이프라인 흐름을 통제합니다. 루프 최적화 및 상태 분기를 책임집니다.
- **Modular Services (`services/chat/`)**:
  - `parser.py`: LLM과 정규표현식을 조합하여 사용자 입력을 구조화(`ParsedUserRequest`)합니다.
  - `run_exaone.py`: RunPod Serverless 비동기 호출 및 Status Polling을 수행하여 EXAONE 모델과 통신합니다.
- **RetrievalService (`retrieval_service.py`)**: 로컬 FAISS 인덱스를 로드하고 임베딩 벡터로 1차 유사도 검색을 수행합니다.

### 3.3 Repositories (`repository/`)
- 데이터베이스 접근 로직을 전담합니다.
- `common/db.py`에서 생성된 `SQLAlchemy` 엔진 또는 `PyMySQL` Raw Connection을 사용하여 쿼리를 실행합니다.
- `RetrievalRepository`는 `RetrievalService`가 찾은 FAISS Document ID 목록을 기반으로 MySQL에서 실제 자소서 본문을 조회합니다.

---

## 4. 데이터베이스 및 리소스 초기화

- `backend/common/db.py` 모듈이 임포트될 때 필수 환경 변수(`RDB_URL`, `VECTOR_DB_URL`)를 검증하고 기본 Engine을 생성합니다.
- `chat_logic.py` 로드 시 LLM 클라이언트와 FAISS 인덱스(`faiss_index_high/`)가 지연 로딩(Lazy Loading) 또는 전역 변수로 할당됩니다. 첫 요청 시 로딩 딜레이가 발생할 수 있습니다.

---

## 5. 개선 사항 및 향후 로드맵

- **완료된 개선**: 과거 1,000줄 이상의 단일 `chat_logic.py`에서 발생하던 모놀리식 구조의 병목을 Service-Repository 및 Modular 패턴으로 완벽히 분리했습니다.
- **향후 로드맵**:
  - JWT 기반의 인증 파이프라인 도입.
  - 관측성 강화 (전면적인 LangSmith `@traceable` 커버리지 확보).
  - 전역 예외 처리(Global Exception Handler)를 통한 일관된 에러 포맷 제공.

---

*last updated: 2026-04-26 | 조라에몽 팀*
