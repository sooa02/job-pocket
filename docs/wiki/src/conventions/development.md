# 📋 job-pocket 개발 컨벤션

> **프로젝트명:** job-pocket
> **팀명:** 조라에몽
> **스택:** Python 3.12 · FastAPI · Streamlit · MySQL 9 · Docker · Docker Compose · RunPod

---

## 목차

1. [폴더 구조](#1-폴더-구조)
2. [명명 규칙](#2-명명-규칙)
3. [Git Branch 전략](#3-git-branch-전략)
4. [커밋 컨벤션](#4-커밋-컨벤션)
5. [코드 리뷰 규칙](#5-코드-리뷰-규칙)

---

## 1. 폴더 구조

```
job-pocket/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── feature_request.md
│   │   └── bug_report.md
│   └── PULL_REQUEST_TEMPLATE.md
│
├── docs/
│   ├── wiki/
│   │   ├── backend/
│   │   │   ├── architecture.md
│   │   │   ├── database.md
│   │   │   └── test.md
│   │   ├── frontend/
│   │   │   ├── architecture.md
│   │   │   └── test.md
│   │   ├── model/
│   │   │   ├── rag_pipeline.md
│   │   │   ├── prompt.md
│   │   │   └── test.md
│   │   └── troubles/
│   ├── readme/
│   └── ppt/
│
├── infra/
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── resume.py
│   │   │       └── user.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── .env.example
├── .gitignore
├── CONVENTIONS.md
└── README.md
```

---

## 2. 명명 규칙

### 2-1. Python 코드

| 대상 | 규칙 | 예시 |
|---|---|---|
| 변수 | `snake_case` | `user_id`, `resume_text` |
| 함수 | `snake_case` | `get_resume_feedback()` |
| 클래스 | `PascalCase` | `ResumeService`, `UserRepository` |
| 상수 | `UPPER_SNAKE_CASE` | `MAX_RETRY`, `DB_POOL_SIZE` |
| 파일명 | `snake_case.py` | `resume_service.py` |
| 디렉토리 | `snake_case` | `resume_service/` |
| Private 멤버 | `_snake_case` | `_parse_resume()` |
| Pydantic 스키마 | `PascalCase` + 접미사 | `ResumeCreateRequest`, `ResumeResponse` |

```python
# ✅ 올바른 예시
class ResumeService:
    MAX_CHUNK_SIZE = 512

    def __init__(self, db_session: Session):
        self._db = db_session

    def get_feedback(self, resume_id: int) -> ResumeResponse:
        resume_text = self._fetch_resume(resume_id)
        return self._build_response(resume_text)

# ❌ 잘못된 예시
class resumeservice:           # PascalCase 아님
    def GetFeedback(self):     # camelCase 사용
        resumeText = "..."     # camelCase 변수
```

### 2-2. 환경변수 / .env

```dotenv
# 형식: UPPER_SNAKE_CASE, 모듈_항목 구조
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=job_pocket_db
MYSQL_USER=jp_user
MYSQL_PASSWORD=

RUNPOD_API_KEY=
RUNPOD_ENDPOINT_ID=

APP_ENV=development         # development | staging | production
APP_SECRET_KEY=
APP_DEBUG=true
```

> ⚠️ `.env` 파일은 절대 커밋하지 않습니다. `.env.example` 만 커밋합니다.

### 2-3. MySQL 테이블 / 컬럼

| 대상 | 규칙 | 예시 |
|---|---|---|
| 테이블명 | `snake_case`, 복수형 | `users`, `resume_feedbacks` |
| 컬럼명 | `snake_case` | `created_at`, `user_id` |
| PK | `id` (AUTO_INCREMENT) | `id BIGINT UNSIGNED` |
| FK | `{참조테이블_단수형}_id` | `user_id`, `resume_id` |
| 타임스탬프 | `created_at`, `updated_at` | `DATETIME DEFAULT CURRENT_TIMESTAMP` |
| 인덱스 | `idx_{테이블}_{컬럼}` | `idx_resumes_user_id` |
| 유니크 | `uq_{테이블}_{컬럼}` | `uq_users_email` |

### 2-4. API 엔드포인트

```
# RESTful, kebab-case, 소문자
GET    /api/v1/resumes
GET    /api/v1/resumes/{resume_id}
POST   /api/v1/resumes
PUT    /api/v1/resumes/{resume_id}
DELETE /api/v1/resumes/{resume_id}

GET    /api/v1/resumes/{resume_id}/feedbacks
POST   /api/v1/resumes/{resume_id}/feedbacks
```

### 2-5. Docker / 인프라

| 대상 | 규칙 | 예시 |
|---|---|---|
| 컨테이너명 | `jp-{서비스명}` | `jp-backend`, `jp-mysql` |
| 이미지 태그 | `job-pocket/{서비스}:{버전}` | `job-pocket/backend:1.0.0` |
| 볼륨명 | `jp_{서비스}_data` | `jp_mysql_data` |
| 네트워크명 | `jp-{영역}-net` | `jp-public-net`, `jp-private-net` |
| 환경변수 (compose) | `UPPER_SNAKE_CASE` | `MYSQL_ROOT_PASSWORD` |

---

## 3. Git Branch 전략

**GitHub Flow** 기반 (main 단일 배포 브랜치)

```
main
 └── dev
      ├── feat/back/{기능}       ← 백엔드 기능 단위 브랜치
      │   ├── feat/back/auth
      │   ├── feat/back/resume
      │   └── feat/back/feedback
      ├── feat/front/{기능}      ← 프론트엔드 기능 단위 브랜치
      │   └── feat/front/resume-upload
      ├── feat/llm/{기능}        ← LLM · RAG 기능 단위 브랜치
      │   ├── feat/llm/rag-pipeline
      │   └── feat/llm/prompt
      ├── infra/{작업}           ← 인프라 작업
      │   └── infra/docker-compose
      ├── fix/{티켓}-{설명}
      └── hotfix/{티켓}-{설명}
```

> ⚠️ `feat/back`, `feat/front`, `feat/llm` 브랜치 자체는 만들지 않습니다.
> Git 특성상 상위 브랜치가 존재하면 하위 브랜치를 만들 수 없습니다.
> 반드시 `feat/back/{기능}` 형태로 바로 생성합니다.

### 3-1. 브랜치 종류

| 브랜치 | 설명 | 생성 위치 | 머지 위치 |
|---|---|---|---|
| `main` | 배포용 (항상 동작) | - | - |
| `dev` | 통합 개발 브랜치 | `main` | `main` (릴리즈 시) |
| `feat/back/{기능}` | 백엔드 기능 개발 | `dev` | `dev` |
| `feat/front/{기능}` | 프론트엔드 기능 개발 | `dev` | `dev` |
| `feat/llm/{기능}` | LLM · RAG 기능 개발 | `dev` | `dev` |
| `infra/{작업}` | 인프라 · DevOps | `dev` | `dev` |
| `fix/{티켓}-{설명}` | 버그 수정 | `dev` | `dev` |
| `hotfix/{티켓}-{설명}` | 긴급 운영 수정 | `main` | `main` + `dev` |
| `release/v{버전}` | 배포 준비 | `dev` | `main` + `dev` |
| `docs/{티켓}-{설명}` | 문서 작업 | `dev` | `dev` |

### 3-2. 브랜치 운영 규칙

```
✅ feat/*/* → dev PR 머지 시 squash merge 사용
✅ dev → main PR 머지 시 merge commit 사용 (이력 보존)
✅ 브랜치 머지 후 즉시 원격 브랜치 삭제
✅ main, dev 브랜치 직접 push 금지
✅ PR 없이 머지 금지
❌ feat/back, feat/front, feat/llm 단독 브랜치 생성 금지
```

### 3-3. 작업 흐름

```bash
# 1. dev 최신화
git checkout dev
git pull origin dev

# 2. 기능 브랜치 생성
git checkout -b feat/back/auth

# 3. 작업 후 커밋
git add .
git commit -m "feat(auth): JWT 토큰 발급 구현

Closes #JP-001"

# 4. 원격 push 후 PR 생성 (타겟: dev)
git push origin feat/back/auth
```

---

## 4. 커밋 컨벤션

**Conventional Commits** 준수

### 4-1. 형식

```
{type}({scope}): {subject}

{body}         ← 선택사항

Closes #{이슈키}
```

### 4-2. Type 목록

| Type | 설명 | 예시 |
|---|---|---|
| `feat` | 새로운 기능 | `feat(resume): 이력서 업로드 API 추가` |
| `fix` | 버그 수정 | `fix(auth): 토큰 만료 처리 누락 수정` |
| `docs` | 문서 수정 | `docs(readme): 로컬 실행 방법 추가` |
| `style` | 코드 포맷팅 (로직 변경 없음) | `style(resume): black 포맷터 적용` |
| `refactor` | 리팩토링 (기능 변경 없음) | `refactor(service): 중복 로직 함수 분리` |
| `test` | 테스트 추가·수정 | `test(resume): 업로드 API 단위테스트 추가` |
| `chore` | 빌드, 패키지, 설정 변경 | `chore(deps): fastapi 업그레이드` |
| `infra` | 인프라, Docker, CI/CD | `infra(docker): MySQL healthcheck 추가` |
| `perf` | 성능 개선 | `perf(query): 이력서 조회 쿼리 인덱스 추가` |
| `revert` | 커밋 되돌리기 | `revert: feat(resume): 업로드 API 추가` |

### 4-3. Scope 목록

```
resume      이력서 관련
user        사용자 관련
auth        인증/인가
feedback    피드백 관련
rag         RAG 파이프라인
model       LLM · 임베딩 모델
mysql       DB 스키마/쿼리
docker      컨테이너 설정
infra       인프라 전반
api         API 라우터
config      설정 파일
```

### 4-4. 커밋 예시

```bash
# ✅ 올바른 예시
feat(resume): POST /api/v1/resumes 엔드포인트 구현

multipart/form-data로 PDF 파일 업로드 처리
MySQL에 메타데이터 저장 후 resume_id 반환

Closes #JP-001

# ✅ 간단한 변경
fix(mysql): 커넥션 풀 최대값 20으로 상향

Closes #JP-015

# ✅ Breaking Change
feat(api)!: /api/v1 → /api/v2 버전 변경

BREAKING CHANGE: v1 엔드포인트 지원 종료

Closes #JP-042

# ❌ 잘못된 예시
fixed bug               # type 없음
WIP                     # 의미 없는 커밋
수정                     # scope 없음
feat: 여러 기능 한번에    # 단일 책임 위반
```

### 4-5. AI로 커밋 메시지 작성하기

ChatGPT 또는 Claude에 아래 프롬프트를 사용합니다.

```
아래 변경사항을 보고 커밋 메시지를 작성해줘.

규칙:
- 형식:
  {type}({scope}): {작업 내용}

  Closes #JP-{이슈번호}

- type: feat, fix, docs, style, refactor, test, chore, infra, perf 중 하나
- scope: resume, user, auth, feedback, rag, model, mysql, docker, infra, api, config 중 하나
- subject는 50자 이내, 한글 사용 가능
- 하나의 커밋 = 하나의 논리적 변경

이슈번호: {JP-XXX}
변경사항:
{git diff 또는 작업 내용 설명}
```

### 4-6. 커밋 규칙 요약

```
✅ 하나의 커밋 = 하나의 논리적 변경
✅ subject는 50자 이내, 현재형 동사 사용
✅ 한글 사용 허용
✅ 이슈 키는 footer에 "Closes #JP-XXX" 형식으로 작성
❌ "WIP", "수정", "test" 같은 무의미한 커밋 금지
❌ 여러 기능을 하나의 커밋에 묶기 금지
❌ Closes 없는 커밋 금지
```

---

## 5. 코드 리뷰 규칙

PR은 **GitHub Actions 자동화** 기반으로 운영합니다.
Actions 전체 통과 = 머지 가능입니다.

```
PR 생성
  │
  ▼
[GitHub Actions] 자동 실행
  ├── CI (lint · format · type)
  ├── Security (secret scan)
  └── AI Review (openai-pr-reviewer)
  │
  ├─ ❌ CI / Security 실패 → 머지 차단, 작성자가 수정 후 재push
  └─ ✅ 전체 통과 → 작성자가 직접 머지
```

### 5-1. GitHub Actions 구성

| 검사 항목 | 도구 | 머지 블로킹 |
|---|---|---|
| 코드 포맷 | `black`, `isort` | ✅ |
| 정적 분석 | `ruff` | ✅ |
| 타입 체크 | `mypy` | ❌ (단계적 적용) |
| 시크릿 탐지 | `gitleaks` | ✅ |
| AI 코드 리뷰 | `openai-pr-reviewer` | ❌ (참고용) |

### 5-2. PR 규칙

**PR 제목 형식:**
```
[JP-001] feat(resume): 이력서 업로드 API 구현
[JP-015] fix(mysql): 커넥션 풀 누수 수정
```

**PR 체크리스트:**
```
- [ ] 커밋 메시지 컨벤션을 지켰는가?
- [ ] .env 파일이나 시크릿이 포함되지 않았는가?
- [ ] PR 설명에 변경 사항과 이유를 작성했는가?
- [ ] GitHub Actions (CI · Security) 전체 통과했는가?
```

**PR 크기 기준:**

| 크기 | 변경 라인 |
|---|---|
| 🟢 Small | ~200줄 |
| 🟡 Medium | 200~500줄 |
| 🔴 Large | 500줄+ (지양) |

### 5-3. 사람이 확인해야 할 항목

```
로직·설계
  □ 비즈니스 요구사항대로 동작하는가?
  □ 엣지케이스(빈 값, null, 대용량)를 처리하는가?
  □ 계층 분리(api → service → repository)가 올바른가?

성능
  □ N+1 쿼리가 발생하지 않는가?
  □ 불필요한 DB 호출이나 반복 연산이 없는가?

가독성
  □ 명명 규칙을 준수하는가?
  □ 복잡한 로직에 주석이 있는가?
  □ 불필요한 print문, 임시 코드가 없는가?
```

---

*last updated: 2026-04-18 | 조라에몽 팀 | 조라에몽*