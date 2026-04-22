# 🧪 Job-Pocket 테스트 인프라 안내

> **문서 목적**: v0.2.0에서 구축한 테스트 계획·코드·평가 시스템·CI 자동화의 구성과 활용 방법을 팀원이 한눈에 파악할 수 있도록 안내한다.
> **작성일**: 2026-04-22
> **버전**: v0.2.0
> **작성자**: 조라에몽 팀

---

## 1. 한 줄 요약

채점 기준 ④ **"테스트 계획 및 결과 보고서"**를 충족시키기 위해, **계획 문서 + 실제 실행 가능한 pytest 코드 + RAG 평가 시스템 + CI 자동화**를 통합 구축한 테스트 인프라다.

---

## 2. 전체 구조 한눈에 보기

### 2.1 파일 배치도

```
job-pocket/
│
├── 📄 pytest.ini                            ← pytest 전역 설정
│
├── ⚙️ .github/workflows/
│   └── ci.yml                               ← GitHub Actions 자동 테스트
│
├── 🐍 backend/tests/                        ← pytest 테스트 코드
│   ├── __init__.py, README.md, conftest.py
│   ├── api/
│   │   ├── test_health.py                   ← /health/z 테스트
│   │   ├── test_auth_api.py                 ← 로그인/회원가입
│   │   ├── test_resume_api.py               ← 이력 정보
│   │   └── test_chat_api.py                 ← 채팅 + RAG 파이프라인
│   ├── integration/
│   │   ├── test_e2e_pipeline.py             ← End-to-End 시나리오
│   │   └── test_retriever.py                ← HybridRetriever
│   └── fixtures/test_users.json             ← 테스트 데이터
│
├── 🧪 evaluation/                           ← RAG 품질 평가 시스템
│   ├── README.md                            ← 사용 가이드
│   ├── utils.py                             ← 지표 계산 함수
│   ├── run_retrieval_eval.py                ← 검색 품질 평가 (CLI)
│   ├── run_generation_eval.py               ← 생성 품질 평가 (CLI)
│   ├── datasets/golden_qa.jsonl             ← 골든 셋 5건
│   └── results/REPORT.md                    ← 결과 리포트 템플릿
│
└── 📝 docs/wiki/test/                       ← 테스트 문서
    ├── README.md                            ← 본 문서
    ├── test_plan.md                         ← 테스트 계획서
    └── performance_report.md                ← 성능 테스트 보고서
```

### 2.2 규모 요약

| 구분 | 파일 수 | 라인 수 |
|---|---|---|
| 계획·보고 문서 | 3 | ~820 |
| pytest 테스트 코드 | 11 | ~1,500 |
| RAG 평가 스크립트 | 6 | ~1,600 |
| CI 설정 | 1 | ~270 |
| **합계** | **21** | **~4,190** |

---

## 3. 파일별 상세 설명

### 3.1 `pytest.ini` — pytest 전역 설정 (47줄)

테스트 파일을 어디서 찾을지, 어떤 마커를 사용할지 정의한다.

```ini
testpaths = backend/tests
pythonpath = backend
markers =
    integration: 통합 테스트
    api: API 엔드포인트 테스트
    mock_llm: LLM 모킹된 테스트
    retriever: FAISS 인덱스 필요
    requires_llm: 실제 LLM API 호출 필요 (평가용)
```

**왜 필요한가**: 이 파일 없이는 `pytest` 명령어가 무엇을 어디에서 실행할지 알 수 없다.

---

### 3.2 `.github/workflows/ci.yml` — CI 자동화 (272줄)

PR 생성 시 GitHub가 자동으로 실행하는 4가지 작업을 정의한다.

| Job | 수행 내용 |
|---|---|
| `lint` | `ruff`로 코드 스타일 검사 |
| `test` | `pytest` 자동 실행 (MySQL 9 컨테이너도 자동 기동) |
| `docker-build` | Dockerfile 빌드 검증 |
| `ci-summary` | PR 본문에 결과 요약 댓글 자동 작성 |

**왜 중요한가**:
- "테스트 자동화 체계"를 채점관에게 보이는 명확한 증거
- 팀원이 실수로 버그 있는 코드를 머지하는 것을 방지
- `docs/wiki/CONVENTIONS.md` 5장 "코드 리뷰 규칙"의 요구사항 충족

---

### 3.3 `backend/tests/` — pytest 테스트 코드 (1,500줄)

실제로 실행 가능한 **51개 테스트 함수**를 포함한다. 단위 테스트 없이 **통합 테스트 중심**으로 작성하여 짧은 기간에 핵심 시나리오를 커버한다.

#### 3.3.1 `conftest.py` — 공용 fixture (277줄)

모든 테스트가 공유하는 준비물.

| Fixture | 설명 |
|---|---|
| `client` | FastAPI TestClient 인스턴스 |
| `clean_db` | 각 테스트마다 깨끗한 DB 제공 |
| `test_user` | 사전 가입된 테스트 유저 |
| `sample_user_info` | 로그인 응답 형식의 5-tuple |
| `mock_llm_responses` | LLM API 호출을 고정 응답으로 대체 |
| `mock_retriever` | FAISS 없이도 Retriever 테스트 가능 |
| `logged_in_client` | 로그인 완료된 클라이언트 |
| `setup_test_env` | 환경변수 자동 설정 |

#### 3.3.2 `api/` — API 엔드포인트 테스트

각 FastAPI 엔드포인트의 HTTP 응답 형식을 검증한다.

| 파일 | 검증 대상 | 테스트 수 | 관련 TC |
|---|---|---|---|
| `test_health.py` | `GET /health/z` | 5개 | TC-028 |
| `test_auth_api.py` | 회원가입·로그인·비밀번호 재설정 | 14개 | TC-001~005 |
| `test_resume_api.py` | 이력 정보 조회/저장 | 9개 | TC-006~008 |
| `test_chat_api.py` | 채팅 이력 + 6단계 RAG 파이프라인 | 12개 | TC-009~017 |

#### 3.3.3 `integration/` — 통합 시나리오 테스트

여러 API를 순차 호출하는 실제 사용자 시나리오를 검증한다.

| 파일 | 시나리오 | 관련 TC |
|---|---|---|
| `test_e2e_pipeline.py` | 회원가입 → 로그인 → 이력저장 → 자소서생성 | TC-018~022 |
| `test_retriever.py` | HybridRetriever의 FAISS + MySQL 검색 | TC-023~025 |

#### 3.3.4 왜 통합 테스트만인가

짧은 개발 기간을 고려하여, 함수 단위 검증(단위 테스트)보다 실제 사용자 시나리오 전체가 동작하는지 확인하는 것이 투자 대비 효과가 높다고 판단했다. 테스트 계획서의 전략과 일치한다.

---

### 3.4 `evaluation/` — RAG 품질 평가 시스템 (1,603줄)

RAG의 품질을 정량 지표로 측정하는 CLI 스크립트 모음이다.

#### 3.4.1 `datasets/golden_qa.jsonl` — 골든 셋 (5건)

"이 쿼리에 대해 이 자소서가 정답이다"라는 어노테이션된 정답 데이터.

```json
{
  "query_id": "Q001",
  "user_profile": {...},
  "company": "네이버",
  "job": "백엔드",
  "question_type": "motivation",
  "relevant_doc_ids": [12, 47, 89]
}
```

v0.3.0에서 20~30건으로 확장 예정이다.

#### 3.4.2 `run_retrieval_eval.py` — 검색 품질 평가 (335줄)

**질문**: HybridRetriever가 정답 자소서를 상위 K개 안에 잘 찾아내는가?

측정 지표는 다음과 같다.

| 지표 | 의미 | 목표 |
|---|---|---|
| Recall@3 | 정답이 상위 3개에 포함되는 비율 | ≥ 0.60 |
| Recall@5 | 상위 5개에 포함 비율 | ≥ 0.75 |
| MRR | 정답의 평균 역순위 | ≥ 0.45 |
| nDCG@3 | 순위 가중 누적 점수 | ≥ 0.55 |

실행 예시:

```bash
python evaluation/run_retrieval_eval.py --top-k 3 5 10 --verbose
```

#### 3.4.3 `run_generation_eval.py` — 생성 품질 평가 (524줄)

**질문**: 생성된 자소서가 실제로 좋은가?

측정 항목:

| 항목 | 측정 방법 | 목표 |
|---|---|---|
| 품질 검증 통과율 | `score_local_draft` 1회 통과 | ≥ 75% |
| 과장 표현 포함률 | 9가지 금지 표현 검출 | ≤ 5% |
| 글자수 달성률 | 목표 ±15% 이내 | ≥ 90% |
| LLM-as-Judge | GPT-4o-mini 5기준 1~5점 | ≥ 3.5/5 |

실행 예시:

```bash
# 비용 절감 모드 (Judge 스킵)
python evaluation/run_generation_eval.py --limit 5 --skip-judge

# 전체 평가 (~$2 비용)
python evaluation/run_generation_eval.py
```

#### 3.4.4 `utils.py` — 공용 지표 계산 함수 (280줄)

Recall@K, MRR, nDCG@K, 과장 표현 검출, 글자수 달성 판정 등의 계산 로직을 재사용 가능한 함수로 제공한다.

#### 3.4.5 `results/REPORT.md` — 결과 리포트 템플릿 (264줄)

v0.3.0에서 실제 평가를 실행하고 나면 지표 값이 자동으로 채워질 템플릿이다. 베이스라인 비교(BM25 vs FAISS, RAG vs LLM 단독) 섹션도 포함한다.

#### 3.4.6 왜 중요한가

- 채점 기준 ③ "RAG 구현"의 **품질 증명 근거**
- "우리는 RAG가 잘 돌아간다는 것을 숫자로 보여줄 준비가 되어 있다"는 체계적 증거
- 향후 성능 회귀 모니터링의 기반

---

### 3.5 `docs/wiki/test/` — 테스트 문서

#### 3.5.1 `test_plan.md` — 테스트 계획서 (376줄)

**"무엇을, 언제, 어떻게 테스트할 것인가"**의 마스터 문서.

주요 내용:

- 테스트 전략 (통합 중심, 단위 테스트 제외)
- 4가지 테스트 유형 (통합 / API / RAG / 수동)
- 위험 기반 우선순위 (P0 / P1 / P2)
- 통과 기준 (지표별 목표값과 최소 허용값)
- 2주 집중 실행 일정 (Gantt 차트)
- 8가지 리스크와 완화 전략
- v0.2.0 Exit Criteria (최소 달성 조건)

채점 기준 ④ "계획" 부분의 핵심 산출물. IEEE 829 표준 형식을 따른다.

#### 3.5.2 `performance_report.md` — 성능 테스트 보고서 (384줄)

v0.4.0에서 수행할 성능 측정 계획과 v0.2.0 베이스라인 관찰 결과.

주요 내용:

- 응답 시간 목표 (p50 / p95 / p99)
- 동시성 목표 (50명 동시 처리)
- 6가지 시나리오 (헬스체크 → 30분 지속 부하)
- 예상 병목 분석 (EXAONE Draft, 임베딩 CPU, MySQL 커넥션)
- 5단계 실행 계획 (Phase 1~5)

---

## 4. 설계 철학

### 4.1 채점 기준 대응

| 채점 기준 | 이 작업의 충족 방식 |
|---|---|
| ② 시스템 아키텍처 | (별도 완료, `docs/wiki/core`에 푸시) |
| ③ RAG 구현 | `evaluation/`으로 품질 측정 체계 증명 |
| ④ 테스트 계획 + 결과 | 본 인프라 전체가 여기에 해당 |

### 4.2 단순 문서가 아닌 실행 가능 시스템

**문서와 코드가 1:1로 대응**한다.

- `test_plan.md` (전략) ↔ `backend/tests/` (실제 pytest 코드)
- `test_cases.md`의 TC-001 ~ TC-032 ↔ 실제 pytest 함수들
- 나중에 실제로 실행하여 결과 수치를 보고서에 채울 수 있는 구조

### 4.3 현실적 제약의 정직한 반영

v0.2.0 시점의 치명적 버그(D-001: `main.py` 라우터 주석)를 인지한 상태에서 설계되었다.

- 테스트 코드는 **버그 수정 후 실행 가능**하도록 작성
- 문서에는 **현재 Blocked 상태를 정직하게 기록**
- "버그 해결 → 테스트 통과 → 지표 측정"의 단계적 로드맵 명시

---

## 5. 사용 방법

### 5.1 테스트 실행 (D-001 수정 후 가능)

```bash
# 레포 루트에서
cd job-pocket

# 의존성 설치
pip install -r docker/backend/requirements.txt

# 전체 테스트 실행
pytest

# 특정 카테고리만
pytest backend/tests/api/
pytest backend/tests/integration/

# FAISS 인덱스 없이 실행
pytest -m "not retriever"

# 커버리지 리포트 포함
pytest --cov=backend --cov-report=html
```

### 5.2 RAG 평가 실행 (v0.3.0 이후)

```bash
# Retrieval 품질
python evaluation/run_retrieval_eval.py --verbose

# Generation 품질 (저비용)
python evaluation/run_generation_eval.py --limit 5 --skip-judge

# 결과 확인
cat evaluation/results/REPORT.md
```

### 5.3 CI 활성화

`.github/workflows/ci.yml`은 PR 생성 시 자동으로 실행된다. 별도 설정 불필요. PR에 결과 요약 댓글이 자동으로 달린다.

---

## 6. 팀원을 위한 Quick Start

### 6.1 역할별 주목해야 할 파일

| 역할 | 주목할 파일 |
|---|---|
| 백엔드 담당 | `backend/tests/api/`, `backend/tests/integration/` |
| LLM 담당 | `evaluation/`, `docs/wiki/model/test.md` |
| 인프라 담당 | `.github/workflows/ci.yml`, `docs/wiki/test/performance_report.md` |
| 전원 | `docs/wiki/test/test_plan.md`, 본 문서 |

### 6.2 개발 중 새 기능 추가 시

1. 기능 구현 후 `backend/tests/api/test_xxx_api.py`에 테스트 케이스 추가
2. 로컬에서 `pytest` 실행하여 통과 확인
3. PR 생성하면 CI가 자동으로 검증
4. 전체 통과 시 `docs/wiki/test/test_cases.md`에도 TC 추가 (v0.3.0 이후)

---

## 7. 알려진 제약 및 해결 계획

### 7.1 테스트 실행을 막는 요소

| 결함 | 영향 | 해결 시점 |
|---|---|---|
| D-001: `main.py` 라우터 주석 | 모든 API 테스트 차단 | v0.2.1 즉시 |
| D-002: `database.py` SQLite 사용 | DB 테스트 환경 불일치 | v0.3.0 |
| D-003: `api_client.py` BASE_URL 하드코딩 | Docker 배포 시 문제 | v0.3.0 |
| D-004: FAISS 인덱스 부재 | Retriever 테스트 차단 | v0.3.0 |

### 7.2 v0.3.0 이후 수행 예정

- 골든 셋 20~30건 확장
- Retrieval·Generation 평가 정식 수행
- `evaluation/results/REPORT.md` 실제 지표 채움
- 성능 테스트 베이스라인 측정

---

## 8. 관련 문서

| 문서 | 경로 |
|---|---|
| 테스트 계획서 (상세) | `docs/wiki/test/test_plan.md` |
| 성능 테스트 보고서 | `docs/wiki/test/performance_report.md` |
| RAG 평가 가이드 | `evaluation/README.md` |
| 테스트 코드 실행 가이드 | `backend/tests/README.md` |
| 개발 컨벤션 | `docs/wiki/CONVENTIONS.md` |
| 시스템 아키텍처 | `docs/wiki/architecture/overview.md` |

---

## 9. 기여 가이드

### 9.1 테스트 추가 시

- 기존 테스트 스타일을 따를 것
- 한글 docstring 허용
- 테스트 함수명은 `test_` 접두사
- `@pytest.mark.api` 또는 `@pytest.mark.integration` 마커 필수
- LLM 호출이 있으면 `@pytest.mark.mock_llm` 마커 추가

### 9.2 평가 스크립트 수정 시

- 새 지표 추가는 `evaluation/utils.py`에 함수 작성
- CLI 옵션 추가는 `--help`에 반영
- 결과 포맷 변경 시 `REPORT.md` 템플릿도 동기화

---

## 10. 개정 이력

| 버전 | 날짜 | 주요 변경 |
|---|---|---|
| 0.1 | 2026-04-22 | 초판 작성. v0.2.0 테스트 인프라 구축 완료 |

---

*last updated: 2026-04-22 | 조라에몽 팀*
