<div align="center">


# 👛 Job Pocket

### 조라에몽의 만능 도구들처럼, 취업 준비생에게 필요한 모든 도구를 한 주머니에

**RAG(Retrieval-Augmented Generation) 기반 AI 자소서 초안 생성 서비스**

취업준비생이 자기소개서를 작성하기 위한 정보를 입력하면, <br/>채용 공고 데이터를 기반으로 맞춤형 피드백을 제공합니다. <br/>단순한 맞춤법 교정이 아닌, 직무 적합성과 표현의 설득력까지 분석합니다.

<br/>

[🚀 빠른 시작](#-설치--실행) · [📖 사용 가이드](#-사용-가이드) · [🏗️ 아키텍처](#️-아키텍처)

</div>

---

## ✨ 주요 기능

| 기능 | 설명 |
|---|---|
| 📄 **자소서 초안 생성** | 업로드한 정보를 기반으로 섹션별로 파싱하여 구조화 후 생성 |
| 🔍 **RAG 기반 피드백** | 채용 공고 DB에서 관련 내용을 검색하여 맞춤 피드백 생성 |
| 🤖 **AI 피드백 생성** | EXAONE 3.5 7.8B 모델을 통한 구체적이고 실용적인 개선안 제시 |
| 💬 **대화형 인터페이스** | 피드백 결과에 대해 AI와 분석 / 보완 가능 |
| 📊 **대화 기록** | 대화 내역 기록 |

---

## 👥 팀원

> **조라에몽** 팀 — SK Networks 26기 3차 프로젝트

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/dhksrlghd">
        <img src="https://github.com/dhksrlghd.png" width="80px" style="border-radius:50%"/><br/>
        <sub><b>홍완기</b></sub><br/>
        <sub>@dhksrlghd</sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/sooa02">
        <img src="https://github.com/sooa02.png" width="80px" style="border-radius:50%"/><br/>
        <sub><b>최수아</b></sub><br/>
        <sub>@sooa02</sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/rusidian">
        <img src="https://github.com/rusidian.png" width="80px" style="border-radius:50%"/><br/>
        <sub><b>장한재</b></sub><br/>
        <sub>@rusidian</sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/Gloveman">
        <img src="https://github.com/Gloveman.png" width="80px" style="border-radius:50%"/><br/>
        <sub><b>이창우</b></sub><br/>
        <sub>@Gloveman</sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/nobrain711">
        <img src="https://github.com/nobrain711.png" width="80px" style="border-radius:50%"/><br/>
        <sub><b>조동휘</b></sub><br/>
        <sub>@nobrain711</sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/JJonyeok2">
        <img src="https://github.com/JJonyeok2.png" width="80px" style="border-radius:50%"/><br/>
        <sub><b>전종혁</b></sub><br/>
        <sub>@JJonyeok2</sub>
      </a>
    </td>
  </tr>
</table>

---

## 🛠️ 기술 스택

### Language & Framework

| 분류 | 기술 | 버전 | 용도 |
|---|---|---|---|
| Language | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) | 3.12 | 전체 백엔드 |
| Frontend | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white) | latest | 사용자 인터페이스 |
| Backend | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) | latest | REST API 서버 |

### Database

| 분류 | 기술 | 용도 |
|---|---|---|
| RDBMS | ![MySQL](https://img.shields.io/badge/MySQL_9.3-4479A1?style=flat-square&logo=mysql&logoColor=white) | 사용자 정보, 이력서 메타데이터 저장 |
| Vector Store | MySQL Vector | 임베딩 벡터 저장 및 유사도 검색 |
| Document Store | MySQL NoSQL | 채용 공고 원문 및 피드백 이력 저장 |

> MySQL 9의 Vector 및 NoSQL 기능을 활용하여 별도의 Vector DB 없이 단일 DB로 통합 관리합니다.

### AI / ML

| 분류 | 모델 | 제공처 | 용도 |
|---|---|---|---|
| LLM | **EXAONE 3.5 7.8B** | LG AI Research via RunPod | 이력서 피드백 생성 |
| Embedding | **Qwen3 Embedding 0.6B** | Alibaba Cloud via RunPod | 텍스트 임베딩 |

### Infrastructure

| 기술 | 용도 |
|---|---|
| ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) | 컨테이너 환경 구성 |
| ![Docker Compose](https://img.shields.io/badge/Docker_Compose-2496ED?style=flat-square&logo=docker&logoColor=white) | 멀티 컨테이너 오케스트레이션 |
| ![RunPod](https://img.shields.io/badge/RunPod-673AB7?style=lat-square&logo=RunPod&logoColor=white) | GPU 기반 LLM / Embedding 서버 호스팅 |

### Co-Tools
| 기술 | 용도 |
|---|---|
| ![JIRA](https://img.shields.io/badge/Jira-0052CC?style=flat&logo=Jira&logoColor=white) | 애자일 프로젝트 스프린트 설정 |
| ![Notion](https://img.shields.io/badge/Notion-000000?style=flat&logo=notion&logoColor=white)| 업무 및 프로젝트 관리 |
| ![Discord](https://img.shields.io/badge/Discord-5865F2?style=flat&logo=discord&logoColor=white) | 업무 메신저 |



---

## 🏗️ 아키텍처

```
                    ┌─────────────┐
                    │    USER     │ 
                    │             │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Streamlit  │  ← Frontend UI
                    │     (FE)    │
                    └──────┬──────┘
                           │ REST API
                    ┌──────▼──────┐
                    │   FastAPI   │  ← Backend Server
                    │     (BE)    │
                    └──────┬──────┘
             ┌─────────────┼─────────────┐
             │             │             │
      ┌──────▼──────┐ ┌────▼────┐ ┌──────▼──────┐
      │  MySQL 9.3  │ │  RAG    │ │  RunPod     │
      │ RDBMS/Vec/  │ │Pipeline │ │ LLM+Embed   │
      │  NoSQL      │ └─────────┘ └─────────────┘
      └─────────────┘
```

### RAG 파이프라인

```
이력서 업로드
     │
     ▼
텍스트 추출 & 전처리
     │
     ▼
Qwen3 0.6B 임베딩 생성
     │
     ▼
MySQL Vector DB에서 유사 채용공고 검색 (Top-K)
     │
     ▼
검색 결과 + 이력서 내용 → EXAONE 3.5 7.8B 프롬프트 구성
     │
     ▼
피드백 생성 및 반환
```

---

## 🚀 설치 & 실행

### 사전 요구사항

- Docker & Docker Compose 설치
- RunPod API Key (LLM 서버 접근용)
- Git

### 방법: Clone하여 실행을 권장

```bash
# 1. 레포지토리 클론
git clone https://github.com/Joraemon-s-Secret-Gadgets/job-pocket.git
cd job-pocket

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값을 입력 (아래 환경 변수 섹션 참고)

# 3. Docker Compose로 전체 서비스 실행
docker compose up -d

# 4. 서비스 접속
# Streamlit UI: http://localhost:8501
# FastAPI Docs: http://localhost:8000/docs
```

### 환경 변수 설정 (`.env`)

```env
# Database
MYSQL_ROOT_PASSWORD=your_root_password
MYSQL_DATABASE=job_pocket
MYSQL_USER=your_db_user
MYSQL_PASSWORD=your_db_password

# LANGSMITH
LANGSMITH_API_KEY=your_langsmith_key

# RunPod (LLM & Embedding)
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_LLM_ENDPOINT=https://api.runpod.ai/v2/{your_llm_pod_id}/runsync
RUNPOD_EMBED_ENDPOINT=https://api.runpod.ai/v2/{your_embed_pod_id}/runsync

# FastAPI
API_HOST=0.0.0.0
API_PORT=8000

# Streamlit
STREAMLIT_PORT=8501
```

### 서비스 상태 확인

```bash
# 전체 컨테이너 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f

# 특정 서비스 로그만 확인
docker compose logs -f backend
docker compose logs -f frontend
```

### 서비스 종료

```bash
# 컨테이너 + 볼륨 삭제 (DB 데이터 포함)
docker compose down -v
```

---

## 📖 사용 가이드

### 1. 회원가입 / 로그인

서비스 접속 후(`http://localhost:8501`) 우측 상단 **[회원가입]** 버튼을 클릭하여 계정을 생성합니다.

### 2. 이력서 업로드

1. 좌측 사이드바에서 **[내 스펙 보관함]** 메뉴 선택
2. 내 정보와 기술 스택, 프로젝트 경험 등 입력
3. 지원하고자 하는 **직무/포지션/문항 정보** 입력 (예: "프론트/백엔드 개발자", "AI 관련 직무")
4. **[채팅 시작]** 버튼 클릭

### 3. AI 피드백 확인

분석이 완료되면 다음 항목별 피드백을 확인할 수 있습니다:

| 항목 | 내용 |
|---|---|
| **직무 적합도** | 입력한 포지션과 이력서 내용의 매칭 점수 및 분석 |
| **경험 기술 방식** | 성과 중심 표현, 수치화, 구체성 개선 제안 |
| **핵심 키워드** | 채용 공고 기반 누락 키워드 및 추가 권장 사항 |
| **항목별 피드백** | 자기소개, 경력, 프로젝트 섹션별 세부 의견 |

### 4. 대화형 심층 분석

피드백 화면 하단의 채팅 입력창을 통해 AI와 추가 대화가 가능합니다.

```
예시 질문:
- "3번 프로젝트 경험을 더 임팩트 있게 표현하려면 어떻게 해야 할까요?"
- "Java 백엔드 포지션에 맞게 기술 스택 섹션을 수정해줄 수 있어요?"
- "현재 이력서의 가장 큰 약점이 뭔가요?"
```

---

## 한계

### 1. 사용자 정보가 부족할 때 결과 일반화 가능성 존재
현재 구조는 문항 유형을 파싱하고 그에 맞게 초안을 생성하도록 되어 있지만, 사용자가 입력하는 정보가 짧거나 스펙 보관함 정보가 충분하지 않으면 결과가 추상적인 문장이나 범용적인 표현으로 흐를 가능성이 있다. 특히 자소서 생성 모델은 빈 정보를 그럴듯한 문장으로 메우려는 경향이 있어서, 이를 프롬프트 제약으로 줄이고 있지만 완전히 해결되지는 않는다. 

### 2. 초기 초안 품질이 로컬 모델 성능에 영향력
초기 초안 생성은 비용 절감을 위해 LG EXAONE 3.5 7.8B 기반 로컬 모델로 처리하도록 설계했다. 이 방식은 장문 초안을 API로 계속 생성하는 것보다 비용 측면에서 유리하지만, 반대로 말하면 첫 초안의 품질은 로컬 모델의 한계에 직접 영향을 받는다. 따라서 표현의 자연스러움이나 문항 적합도 면에서는 후처리 단계에 의존하는 비중이 크다. 

### 3. 수정 흐름은 자연스럽지만, 수정 범위 판단은 아직 단순
현재는 사용자의 후속 입력이 수정 요청인지 키워드 기반으로 판별하고, 직전 결과를 기준으로 수정안을 생성하는 방식이다. 사용자가 실제로는 새 문항을 입력했는데도 수정 요청으로 해석되거나, 반대로 수정 요청인데 새 초안 생성으로 넘어갈 가능성이 있다. 즉 생성과 수정의 분리는 구현했지만, 두 흐름을 구분하는 판단 로직은 아직 정교하지 않다. 

### 4. 평가 결과와 수정 흐름 연결은 구현했지만 평가 자체의 정밀도는 더 보완 필요
현재 결과는 평가 및 코멘트, 보완 포인트, 그리고 보완 포인트를 바로 수정 요청으로 연결하는 흐름까지 갖추고 있다. 다만 평가 자체는 여전히 모델이 만든 텍스트에 의존하는 부분이 있어, 실제 문항 적합성·사실성·문체 안정성 같은 항목을 더 세밀하게 규칙화할 필요가 있다. 


---

## 확장 방향

### 1. 사용자 정보 입력 구조 세분화할 필요성 존재
현재는 경험, 수상, 기술 스택 정도를 큰 텍스트 단위로 받는 구조인데, 이를 프로젝트명, 역할, 문제 상황, 해결 방식, 결과처럼 더 잘게 구조화하면 생성 품질이 올라갈 수 있다. 이렇게 되면 모델이 없는 경험을 추론하기보다, 이미 구조화된 정보를 더 정확하게 조합할 수 있다. 

### 2. 평가를 규칙 기반 점검과 결합 가능
지금은 평가와 보완 포인트도 모델 중심으로 생성되지만, 향후에는 문항 적합성, 글자 수 충족 여부, 과장 표현 여부, 사실성 위반 가능성 등을 규칙 기반으로 함께 점검할 수 있다. 그러면 단순한 자연어 평가보다 더 신뢰도 높은 피드백 구조로 확장할 수 있다. 

### 3. 비용 최적화 구조를 더 발전 가능성 존재
지금도 초기 장문 생성은 로컬 모델, 수정과 정제는 API 모델로 나누어 비용을 줄이는 구조를 적용했다. 앞으로는 문항 유형이나 입력 길이에 따라 어떤 단계까지 로컬에서 처리하고, 어느 시점에만 API를 호출할지 더 세밀하게 분기하면 비용 효율을 더 높일 수 있다. 즉 단순한 모델 분리가 아니라, 요청 특성에 따라 동적으로 생성 비용을 제어하는 방향으로 확장할 수 있다. 

### 4. 결과 화면을 출력이 아니라 작성 워크플로우로 확장 필요
현재, 생성 → 평가 → 보완 포인트 → 수정안 생성 흐름은 구현되어 있다. 이후에는 수정 이력 비교, 버전별 저장, 특정 문단만 선택 수정, 문체 옵션 선택 같은 기능을 붙이면 단순 생성 서비스가 아니라 실제 작성 도구에 가까운 구조로 확장할 수 있다. 

---
## 10. 프로젝트 구조 📁

```
JobPocket/ 
├── backend/                # FastAPI 백엔드
│   ├── auth.py             # 사용자 인증 처리
│   ├── common/             # 공통 유틸리티 및 설정
│   ├── database.py         # DB 연결 및 쿼리 로직
│   ├── exaone/             # EXAONE 모델 관련 처리
│   ├── main.py             # FastAPI 애플리케이션 진입점
│   ├── retriever.py        # RAG 기반 정보 검색
│   ├── routers/            # API 엔드포인트 라우팅
│   ├── schemas/            # Pydantic 데이터 검증 스키마
│   ├── services/           # 핵심 비즈니스 로직 (AI 처리 등)
│   ├── tests/              # 단위 테스트 코드
│   └── utils/              # 기타 백엔드 유틸리티
├── database/               # 데이터베이스 설정
│   ├── init/               # 초기화 스크립트
│   └── my.cnf              # MySQL 설정 파일
├── docker/                 # Docker 관련 파일
│   ├── backend/            # 백엔드 Dockerfile 및 설정
│   ├── database/           # 데이터베이스 Dockerfile 및 설정
│   └── frontend/           # 프론트엔드 Dockerfile 및 설정
├── docs/                   # 프로젝트 문서
│   ├── test_plan_sample.md # 테스트 계획서 샘플
│   └── wiki/               # 아키텍처, ERD 등 위키 문서
├── frontend/               # Streamlit 프론트엔드
│   ├── app.py              # Streamlit 애플리케이션 메인
│   ├── public/             # 정적 리소스 (이미지, 로고 등)
│   ├── utils/              # 프론트엔드 유틸리티 (api_client 등)
│   └── views/              # 화면 UI 구성 요소
├── docker-compose.dev.yaml # 개발용 Docker Compose 설정
├── docker-compose.yaml     # 운영용 Docker Compose 설정
├── LICENSE                 # 프로젝트 라이선스
├── README.md               # 프로젝트 메인 문서
└── runpod_test.py          # RunPod 연동 테스트 스크립트
```
---

## 📌 버전 히스토리

| 버전 | 설명 | 상태 |
|---|---|---|
| `v0.1.0` | Docker Compose 기반 전체 서비스 스택 구축 | ✅ 완료 |
| `v0.2.0` | BE · FE · LLM 통합 | ✅ 완료 |
| `v0.3.0` | 버그 수정 및 안정화 | ✅ 완료 |
| `v0.4.0` | 코드 리팩토링 및 성능 개선 | ⏳ 예정 |
| `v0.5.0` | 배포 및 발표 준비 | ⏳ 예정 |

---

## 🔗 관련 문서

- [백엔드 아키텍처](./docs/wiki/backend/architecture.md)
- [DB 설계 (ERD)](./docs/wiki/backend/database.md)
- [RAG 파이프라인](./docs/wiki/model/rag_pipeline.md)
- [프롬프트 전략](./docs/wiki/model/prompt.md)
- [개발 컨벤션](./docs/wiki/CONVENTIONS.md)
- [트러블슈팅](./docs/wiki/troubles/)

---
### 개인 회고
<table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
    <thead>
        <tr style="background-color: #f8f9fa;">
            <th style="width: 20%; border: 1px solid #ddd; padding: 10px;">이름</th>
            <th style="border: 1px solid #ddd; padding: 10px;">회고</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">최수아</td>
            <td style="border: 1px solid #ddd; padding: 10px;">
</td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">장한재</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">홍완기</td>
            <td style="border: 1px solid #ddd; padding: 10px;">
            </td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">전종혁</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">이창우</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">조동휘</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
    </tbody>
</table>

---

### 팀원 회고

<table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 30px;">
    <thead>
        <tr style="background-color: #f8f9fa;">
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">대상자</th>
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">작성자</th>
            <th style="border: 1px solid #ddd; padding: 10px;">회고 내용</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="5" style="text-align: center; font-weight: bold; border: 1px solid #ddd;">장한재</td>
            <td style="text-align: center; border: 1px solid #ddd;">이창우</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">홍완기</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">최수아</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">전종혁</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">조동휘</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
    </tbody>
</table>
<table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 30px;">
    <thead>
        <tr style="background-color: #f8f9fa;">
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">대상자</th>
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">작성자</th>
            <th style="border: 1px solid #ddd; padding: 10px;">회고 내용</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="5" style="text-align: center; font-weight: bold; border: 1px solid #ddd;">이창우</td>
            <td style="text-align: center; border: 1px solid #ddd;">홍완기</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">장한재</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">최수아</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">전종혁</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">조동휘</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
    </tbody>
</table>
<table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 30px;">
    <thead>
        <tr style="background-color: #f8f9fa;">
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">대상자</th>
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">작성자</th>
            <th style="border: 1px solid #ddd; padding: 10px;">회고 내용</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="5" style="text-align: center; font-weight: bold; border: 1px solid #ddd;">최수아</td>
            <td style="text-align: center; border: 1px solid #ddd;">이창우</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">장한재</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">홍완기</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">전종혁</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">조동휘</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
    </tbody>
</table>
<table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 30px;">
    <thead>
        <tr style="background-color: #f8f9fa;">
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">대상자</th>
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">작성자</th>
            <th style="border: 1px solid #ddd; padding: 10px;">회고 내용</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="5" style="text-align: center; font-weight: bold; border: 1px solid #ddd;">홍완기</td>
            <td style="text-align: center; border: 1px solid #ddd;">이창우</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">장한재</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">최수아</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">전종혁</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">조동휘</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
    </tbody>
</table>
<table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 30px;">
    <thead>
        <tr style="background-color: #f8f9fa;">
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">대상자</th>
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">작성자</th>
            <th style="border: 1px solid #ddd; padding: 10px;">회고 내용</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="5" style="text-align: center; font-weight: bold; border: 1px solid #ddd;">전종혁</td>
            <td style="text-align: center; border: 1px solid #ddd;">이창우</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">장한재</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">최수아</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">홍완기</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">조동휘</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
    </tbody>
</table>
<table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd; margin-bottom: 30px;">
    <thead>
        <tr style="background-color: #f8f9fa;">
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">대상자</th>
            <th style="width: 15%; border: 1px solid #ddd; padding: 10px;">작성자</th>
            <th style="border: 1px solid #ddd; padding: 10px;">회고 내용</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="5" style="text-align: center; font-weight: bold; border: 1px solid #ddd;">조동휘</td>
            <td style="text-align: center; border: 1px solid #ddd;">이창우</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">장한재</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">최수아</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">전종혁</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
        <tr>
            <td style="text-align: center; border: 1px solid #ddd;">홍완기</td>
            <td style="border: 1px solid #ddd; padding: 10px;"></td>
        </tr>
    </tbody>
</table>

---
---

## 📜 License

본 프로젝트는 **MIT License**를 따릅니다.<br/> 
모든 소스 코드 및 관련 문서의 사용 및 배포 규정은 [LICENSE](./LICENSE) 파일에서 확인하실 수 있습니다.
<div align= "center">
Copyright (c) 2026 SK Networks 26th 팀 조라에몽 (Team Joraemon)</div>