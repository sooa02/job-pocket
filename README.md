# 📋  job-pocket

> 조라에몽의 만능 도구들처럼, 취업 준비생에게 필요한 모든 도구를 한 주머니에

RAG 기반 이력서 피드백 서비스입니다.

---

## 기술 스택

| 분류 | 기술 |
|---|---|
| Language | Python 3.12 |
| UI | Streamlit |
| Backend | FastAPI |
| Database | MySQL 9 (RDBMS · Vector · NoSQL 통합) |
| LLM | EXAONE 3.5 7.8B (LG AI Research) via RunPod |
| Embedding | Qwen2.5 7B via RunPod |
| Infra | Docker · Docker Compose · RunPod |

---


## 버전 전략

마일스톤 단위로 버전을 관리합니다. 각 버전은 `release/v{버전}` 브랜치를 통해 `main`에 머지됩니다.

| 버전 | 마일스톤 | 설명 |
|---|---|---|
| `v0.1.0` | 인프라 완료 | Docker Compose 기반 전체 서비스 스택 구축 완료 |
| `v0.2.0` | 통합 | 각 파트(BE · FE · LLM) 사전조사 결과물을 하나의 서비스로 연결 |
| `v0.3.0` | 안정화 | 통합 이후 발견된 치명적 오류 및 버그 수정 |
| `v0.4.0` | 최적화 | 코드 리팩토링 및 성능 개선 |
| `v0.5.0` | 배포 | 수강생 대상 배포 및 발표 가능 수준 |

---

## 개발 워크플로우

### 매일 작업 시작 전

```bash
git checkout develop
git pull origin develop
git checkout feature/be    # 본인 브랜치
git merge develop
```

### 커밋

커밋 메시지는 반드시 **Conventional Commits** 을 준수합니다.

```bash
git add .
git commit -m "feat(resume): POST /api/v1/resumes 엔드포인트 구현


Closes #JP-001"
git push origin feature/be
```

커밋 타입: `feat` · `fix` · `docs` · `style` · `refactor` · `test` · `chore` · `infra` · `perf`

자세한 규칙은 [`CONVENTIONS.md`](./CONVENTIONS.md) 를 참고합니다.

**AI로 커밋 메시지 작성하기**

ChatGPT 또는 Claude에 아래 프롬프트를 사용합니다.

```
아래 변경사항을 보고 커밋 메시지를 작성해줘.

규칙:
- 형식:
  {type}({scope}): {작업 내용}

  Closes #JP-{이슈번호}

- type: feat, fix, docs, style, refactor, test, chore, infra, perf 중 하나
- scope: resume, user, auth, feedback, rag, mysql, docker, infra, api, config 중 하나
- subject는 50자 이내, 한글 사용 가능
- 하나의 커밋 = 하나의 논리적 변경

이슈번호: {JP-XXX}
변경사항:
{git diff 또는 작업 내용 설명}
```

출력 예시:
```
feat(resume): POST /api/v1/resumes 엔드포인트 구현

Closes #JP-001
```

### PR 생성

- 타겟 브랜치: `develop`
- 제목 형식: `[JP-001] feat(resume): 이력서 업로드 API 구현`
- GitHub Actions (CI · Security) 전체 통과 후 머지

---

## 문서 작성 가이드

모든 문서는 `docs/` 하위에 작성합니다.

### docs/wiki — 개발 문서

작업 시작 전 설계 문서를, 완료 후 테스트 문서를 작성합니다.

| 문서 | 경로 | 작성 시점 | 담당 |
|---|---|---|---|
| 백엔드 아키텍처 | `docs/wiki/backend/architecture.md` | 개발 전 | BE |
| DB 설계 (ERD) | `docs/wiki/backend/database.md` | 개발 전 | BE |
| 백엔드 테스트 | `docs/wiki/backend/test.md` | 개발 후 | BE |
| 프론트 아키텍처 | `docs/wiki/frontend/architecture.md` | 개발 전 | FE |
| 프론트 테스트 | `docs/wiki/frontend/test.md` | 개발 후 | FE |
| RAG 파이프라인 | `docs/wiki/model/rag_pipeline.md` | 개발 전 | LLM |
| 프롬프트 전략 | `docs/wiki/model/prompt.md` | 개발 전 | LLM |
| 모델 평가 | `docs/wiki/model/test.md` | 개발 후 | LLM |
| 트러블슈팅 | `docs/wiki/troubles/{파일명}.md` | 이슈 발생 시 | 전원 |

**트러블슈팅 작성 방법**

이슈 하나당 파일 하나를 생성합니다.

```
docs/wiki/troubles/
├── mysql-connection-pool-leak.md
├── qdrant-vector-dimension-mismatch.md
└── chainlit-cors-error.md
```

파일 작성 형식:

```markdown
# {증상 요약}

**증상:**
{에러 메시지 또는 현상}

**원인:**
{원인 분석}

**해결:**
{해결 방법 및 코드}
```

### docs/readme — README 모음

각 컴포넌트별 상세 README를 이 폴더에 작성합니다.

```
docs/readme/
├── backend.md
├── frontend.md
└── model.md
```

### docs/ppt — 발표자료

발표자료 PPT를 pdf로 변환한 파일을 이 폴더에 업로드합니다.

```
docs/ppt/
├── 중간발표_v1.pdf
└── 최종발표_v1.pdf
```


---

## 절대 하면 안 되는 것

```
❌ main 또는 develop에 직접 push
❌ .env 파일 커밋
❌ PR 없이 머지
❌ 이슈 번호 없는 커밋 (Closes #JP-XXX 누락)
```

*last updated: 2026-04-18 | 조라에몽 팀 | 조라에몽*