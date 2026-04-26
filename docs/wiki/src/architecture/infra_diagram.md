# 🐳 Job-Pocket 인프라 구성

> **문서 목적**: Docker Compose 기반 배포 구성, 컨테이너 간 네트워크 토폴로지, 볼륨·포트·환경변수 매핑을 기술한다.
> **작성일**: 2026-04-26
> **버전**: v0.3.0 (mermaid diagram을 image로 수정)
> **관련 파일**: `docker-compose.yaml`, `docker/**/Dockerfile`, `.env.example`

---

## 1. 전체 토폴로지

### 1.1 물리 구성도

![물리 구성도](../assets/images/architecture/infrastructure.png)


### 1.2 3개 서비스 요약

| 서비스 | 역할 | 베이스 이미지 | 공개 포트 |
|---|---|---|---|
| `frontend` | 사용자 UI (Streamlit) | `python:3.12-slim` | 8501 |
| `backend` | API 서버 (FastAPI) | `python:3.12-slim` | 8000 |
| `database` | 영속 저장 (MySQL 9) | `mysql:9.3` | 3306 |

세 서비스는 Docker Compose의 기본 네트워크(`job-pocket_default`)에 자동 가입되어 서비스 이름(`frontend`, `backend`, `database`)을 호스트명으로 사용한다.

---

## 2. docker-compose.yaml 상세

### 2.1 전체 구조

```yaml
name: job-pocket

services:
  backend:
    image: nobrain711/job-pocket:backend-v0.2.0
    ports: ["8000:8000"]
    volumes: [./backend:/app]
    env_file: [.env]
    environment: {...}
    depends_on:
      database:
        condition: service_healthy

  frontend:
    image: nobrain711/job-pocket:frontend-v0.2.0
    ports: ["8501:8501"]
    volumes: [./frontend:/app]
    env_file: [.env]
    environment: {TZ, API_BASE_URL}
    depends_on: [backend]

  database:
    image: nobrain711/job-pocket:database-v0.1.1
    ports: ["3306:3306"]
    env_file: [.env]
    environment: {TZ, MYSQL_ROOT_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-proot"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

volumes:
  mysql_data:
```

### 2.2 시작 순서

`depends_on`의 `condition: service_healthy` 설정으로 Backend는 Database 컨테이너가 healthy 상태가 된 후에만 시작된다. 이를 통해 Backend가 기동 직후 DB 커넥션을 만들다 실패하는 레이스 컨디션을 방지한다. Frontend는 Backend 시작을 기다리되 health 체크 없이 즉시 실행되므로, Frontend가 먼저 뜨더라도 사용자가 API를 호출하는 시점에는 Backend가 준비되어 있다.

---

## 3. 컨테이너별 상세

### 3.1 Backend 컨테이너

**Dockerfile** (`docker/backend/Dockerfile`):

```dockerfile
FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY docker/backend/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**주요 설계 결정**:

`python:3.12-slim`을 선택한 이유는 경량성과 최신 Python 3.12의 성능 개선을 모두 얻기 위함이다. `full` 이미지 대비 약 900MB 절감되며, 개발에 필요한 최소 시스템 패키지(`gcc`, `pkg-config`)만 추가 설치한다.

`PYTHONPATH=/app`은 Backend 코드가 `from routers.x import ...` 같이 루트 기반 import를 사용하기 때문이다. 이 환경변수 설정 없이는 컨테이너 내부에서 module import 에러가 발생한다.

`--reload`는 개발 편의용이다. 소스 변경 시 uvicorn이 자동으로 프로세스를 재시작하므로, volume mount(`./backend:/app`)와 조합하여 로컬 코드 수정이 즉시 반영된다. 운영 배포(v0.5.0)에서는 이 플래그를 제거하고 `--workers 4` 같은 멀티 프로세스 설정으로 전환한다.

### 3.2 Frontend 컨테이너

**Dockerfile** (`docker/frontend/Dockerfile`):

```dockerfile
FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY docker/frontend/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.runOnSave=true"]
```

**주요 설계 결정**:

`--server.address=0.0.0.0`은 컨테이너 외부에서 접속하기 위한 필수 설정이다. Streamlit 기본값인 `localhost`는 컨테이너 내부에서만 바인드되어 호스트에서 접근할 수 없다.

`--server.runOnSave=true`는 소스 변경 시 자동 리로드를 활성화한다. 개발 편의 옵션이며 배포 이미지에서는 제거한다.

`gcc` 같은 빌드 도구를 설치하지 않는다. Frontend는 순수 Python 라이브러리(streamlit, requests, streamlit-extras 등)만 사용하여 네이티브 컴파일이 불필요하다.

### 3.3 Database 컨테이너

**Dockerfile** (`docker/database/Dockerfile`):

```dockerfile
FROM mysql:9.3

COPY database/my.cnf /etc/mysql/conf.d/custom.cnf

RUN microdnf install -y tzdata && microdnf clean all
```

**주요 설계 결정**:

공식 `mysql:9.3` 이미지를 베이스로 사용하여 MySQL 9의 `VECTOR` 타입 등 신기능을 활용한다. v8 이하에서는 VECTOR 지원이 없다.

`my.cnf`를 `/etc/mysql/conf.d/custom.cnf`로 복사하여 기본 설정을 덮어쓴다. 이 설정은 벡터 연산용 메모리 증가, InnoDB 안정성 옵션 활성화, 문자셋 `utf8mb4` 고정 등을 포함한다 (상세: `docs/wiki/backend/database.md`).

`tzdata` 설치는 `TZ` 환경변수를 정상 적용하기 위한 준비로, 한국 타임존(`Asia/Seoul`) 사용 시 필수다.

### 3.4 MySQL 초기화 스크립트

`database/init/` 폴더의 SQL 파일이 MySQL 컨테이너의 `/docker-entrypoint-initdb.d/`로 마운트된다. MySQL 공식 이미지는 이 폴더에 있는 `.sql` 파일을 **파일명 알파벳 순으로** 자동 실행한다. 따라서 실행 순서를 제어하기 위해 번호 접두사를 사용한다.

| 파일 | 내용 |
|---|---|
| `01_create_databases.sql` | `job_pocket_rdb`, `job_pocket_vector` DB 생성 |
| `02_create_users.sql` | `rdb_user`, `vector_user` 생성 및 권한 부여 |
| `03_rdb_tables.sql` | `users`, `chat_history` 테이블 |
| `04_vector_tables.sql` | `companies`, `job_posts`, `applicant_records`, `resume_vectors` 테이블 |

이 스크립트는 `mysql_data` 볼륨이 비어 있을 때만 실행된다. 스키마를 재적용하려면 `docker compose down -v`로 볼륨을 삭제 후 재기동해야 한다.

---

## 4. 네트워크 구성

### 4.1 컨테이너 간 통신

Docker Compose는 프로젝트명(`job-pocket`) 기반의 기본 네트워크를 자동 생성하고 모든 서비스를 참가시킨다. 각 컨테이너는 서비스 이름으로 다른 컨테이너에 접근할 수 있다.

| Source | Target | 방식 | 내부 호스트명 |
|---|---|---|---|
| frontend | backend | HTTP | `http://backend:8000` |
| backend | database | MySQL Protocol | `database:3306` |

Frontend 코드(`utils/api_client.py`)의 `BASE_URL`은 개발 편의상 `http://localhost:8000/api`로 하드코딩되어 있으나, 컨테이너 내부에서는 `backend`라는 서비스명으로 접근해야 한다. v0.3.0에서 환경변수(`API_BASE_URL`)로 분리하여 로컬 개발과 컨테이너 배포 양쪽 모두 지원할 예정이다.

### 4.2 포트 매핑

모든 서비스의 내부 포트가 호스트의 같은 포트로 공개된다. 현재 개발 단계 편의를 위한 설정이며, 배포 단계에서는 Frontend의 8501만 공개하고 나머지는 내부 네트워크로만 접근 가능하게 제한한다.

```
Host:8501 → frontend:8501      (사용자 접속)
Host:8000 → backend:8000       (개발자 API 테스트)
Host:3306 → database:3306      (DB 클라이언트로 직접 접속)
```

---

## 5. 볼륨 관리

### 5.1 Named Volume — `mysql_data`

```yaml
volumes:
  - mysql_data:/var/lib/mysql
```

MySQL의 데이터 디렉토리를 Docker가 관리하는 named volume에 마운트한다. `docker compose down` 시에는 보존되며, `docker compose down -v` 실행 시에만 삭제된다. 운영 환경에서는 명시적으로 로컬 디렉토리(bind mount)를 지정하여 백업 용이성을 확보하는 것이 권장된다.

### 5.2 Bind Mount — 소스 코드 동기화

```yaml
# backend
volumes:
  - ./backend:/app

# frontend
volumes:
  - ./frontend:/app
```

호스트의 `./backend`와 `./frontend` 디렉토리를 컨테이너의 `/app`에 실시간 마운트한다. 개발 중 소스 파일을 수정하면 즉시 컨테이너 내부에 반영되며, `--reload`(Backend)와 `--server.runOnSave`(Frontend)와 결합하여 HMR(Hot Module Replacement)과 유사한 개발 경험을 제공한다.

운영 배포(v0.5.0)에서는 이 bind mount를 제거하고 이미지에 COPY된 소스만 사용한다. 이는 컨테이너가 불변(immutable)해야 하는 원칙과 일치한다.

### 5.3 Init Script Mount

```yaml
- ./database/init:/docker-entrypoint-initdb.d
```

MySQL 초기화 스크립트를 read-only 관점에서 마운트한다. 이는 공식 MySQL 이미지의 관례다.

---

## 6. 헬스체크

### 6.1 Database 헬스체크

```yaml
healthcheck:
  test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-proot"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

10초 간격으로 `mysqladmin ping`을 실행하여 MySQL 서버의 응답 여부를 확인한다. `start_period: 30s`는 컨테이너 기동 직후 30초간은 실패해도 unhealthy로 간주하지 않는 grace period다. MySQL의 초기화에는 일반적으로 15~25초가 소요된다.

### 6.2 Backend 헬스체크 (예정)

v0.2.0 시점에는 Backend 컨테이너에 Docker 레벨 healthcheck가 설정되지 않았다. `GET /health/z` 엔드포인트가 이미 구현되어 있으므로, v0.3.0에서 다음 설정을 추가할 예정이다:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/z"]
  interval: 15s
  timeout: 5s
  retries: 3
  start_period: 60s
```

Backend의 `start_period`는 60초로 둔다. 임베딩 모델 다운로드와 FAISS 인덱스 로드에 시간이 걸리기 때문이다.

---

## 7. 환경변수 관리

### 7.1 `.env.example` 템플릿

```bash
# frontend env
API_BASE_URL=

# backend env
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64)

OPENAI_API_KEY=
RUNPOD_API_KEY=
GROQ_API_KEY=

LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=Job-pocket

# RDB
RDB_URL=mysql+pymysql://rdb_user:rdb_password@database:3306/job_pocket
MYSQL_RDB_USER=rdb_user
MYSQL_RDB_PASSWORD=rdb_password

# Vector DB
VECTOR_DB_URL=mysql+pymysql://vector_user:vector_password@database:3306/job_pocket
MYSQL_VECTOR_USER=vector_user
MYSQL_VECTOR_PASSWORD=vector_password

# database env
MYSQL_ROOT_PASSWORD=root
TIMEZONE=Asia/Seoul
```

### 7.2 주입 방식

각 서비스는 `env_file: - .env` 설정으로 `.env` 파일 전체를 읽어들이고, 추가로 `environment:` 블록에 명시적으로 나열된 변수를 컨테이너 환경변수로 설정한다. 이 이중 구조는 `.env`에 정의된 변수 중 실제로 컨테이너가 필요한 것만 선택적으로 노출하는 효과가 있다.

### 7.3 비밀정보 보호

`.env` 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않는다. 템플릿으로는 `.env.example`만 유지되며, 팀원은 각자 로컬에서 `.env`를 생성해 사용한다. 운영 환경에서는 Docker Secrets 또는 AWS Secrets Manager 같은 보안 저장소로 대체한다.

---

## 8. 이미지 배포 전략

### 8.1 Docker Hub

세 이미지 모두 Docker Hub의 `nobrain711/job-pocket` 저장소에 태그별로 push된다:

| 이미지 | 설명 |
|---|---|
| `backend-v0.2.0` | v0.2.0 시점 백엔드 |
| `frontend-v0.2.0` | v0.2.0 시점 프론트엔드 |
| `database-v0.1.1` | v0.1.1 이후 DB 설정 변경 없음 |

DB 이미지는 `my.cnf`와 초기화 스크립트가 변하지 않았으므로 v0.1.1을 유지한다. 이는 불필요한 재빌드와 네트워크 비용을 절감한다.

### 8.2 멀티 플랫폼 지원

Dockerfile의 `--platform=linux/amd64` 지시자는 M1/M2 Mac 같은 ARM64 환경에서도 amd64 이미지를 빌드하게 강제한다. 이는 배포 대상 서버가 x86_64임을 전제로 한다. 향후 ARM64 서버 지원이 필요하면 `docker buildx` 기반 멀티 아키텍처 빌드로 전환한다.

---

## 9. 실행 절차

### 9.1 최초 실행

```bash
# 1. 레포 클론
git clone -b dev https://github.com/Joraemon-s-Secret-Gadgets/job-pocket.git
cd job-pocket

# 2. 환경변수 설정
cp .env.example .env
vi .env    # API 키 등 입력

# 3. 이미지 pull (Docker Hub에서)
docker compose pull

# 4. 서비스 기동
docker compose up -d

# 5. 상태 확인
docker compose ps
docker compose logs -f backend
```

### 9.2 로컬 빌드 (개발 이미지 수정 시)

```bash
docker compose build
docker compose up -d --force-recreate
```

### 9.3 완전 초기화 (DB 포함)

```bash
docker compose down -v
docker compose up -d
```

---

## 10. 접속 경로

| 리소스 | URL |
|---|---|
| Frontend (사용자 UI) | http://localhost:8501 |
| Backend API | http://localhost:8000 |
| Backend Swagger UI | http://localhost:8000/docs |
| Backend ReDoc | http://localhost:8000/redoc |
| MySQL CLI | `docker exec -it job-pocket-database-1 mysql -uroot -proot` |

---

## 11. 리소스 요구사항

### 11.1 최소 사양

| 리소스 | 권장 최소 | 이유 |
|---|---|---|
| CPU | 4코어 | Backend의 임베딩 연산 (Qwen3 CPU 추론) |
| 메모리 | 8GB | FAISS + MySQL buffer pool + Python 프로세스 |
| 디스크 | 10GB | Docker 이미지 + HuggingFace 모델 캐시 + MySQL 데이터 |

### 11.2 비용 분포 (추정)

- MySQL buffer pool: 약 2GB (my.cnf 설정)
- HuggingFace 모델 가중치: 약 1.2GB (Qwen3-Embedding-0.6B)
- FAISS 인덱스: 수십 MB ~ 수백 MB (샘플 규모에 따름)
- Python 프로세스 + 종속성: 각 컨테이너 500MB ~ 1GB

---

## 12. 알려진 이슈

### 12.1 Frontend의 BASE_URL 하드코딩

`utils/api_client.py`에서 `BASE_URL = "http://localhost:8000/api"`가 하드코딩되어 있다. 컨테이너 내부에서는 `http://backend:8000/api`를 사용해야 한다. 현재는 브라우저가 직접 Backend의 8000 포트에 접근하므로 동작하지만, 컨테이너 네트워킹을 정상화하려면 환경변수로 분리해야 한다.

### 12.2 Backend의 router 등록 누락

`backend/main.py`에서 실제 라우터 등록 코드가 삼중따옴표 주석 안에 갇혀 있다. v0.2.1 핫픽스로 해결 예정이다.

### 12.3 FAISS 인덱스 부재

`faiss_index_high/` 폴더가 이미지에 포함되지 않으며, 기동 시 `FAISS.load_local()`이 실패한다. 인덱스 빌드 스크립트와 함께 v0.3.0에서 해결한다.

---

## 13. 관련 문서

| 주제 | 문서 |
|---|---|
| 시스템 개요 | `docs/wiki/architecture/overview.md` |
| 데이터 플로우 | `docs/wiki/architecture/data_flow.md` |
| DB 상세 | `docs/wiki/backend/database.md` |
| 백엔드 구조 | `docs/wiki/backend/architecture.md` |

---

*last updated: 2026-04-26 | 조라에몽 팀*
