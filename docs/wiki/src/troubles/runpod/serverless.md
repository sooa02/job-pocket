# RunPod Serverless 트러블슈팅 가이드

> **대상 서비스:** Job-Pocket LLM 추론 서버 (EXAONE-3.5-7.8B-Instruct)  
> **런타임:** RunPod Flash (Serverless)  
> **최초 작성일:** 2025-04-25  
> **작성자**: 조동휘

---

## 목차

1. [Flash 패키징(pack) 누락 — `flash_manifest.json not found`](#1-flash-패키징pack-누락--flash_manifestjson-not-found)
2. [401 Unauthorized](#2-401-unauthorized)
3. [Tokenizer 초기화 실패 — `sentencepiece` / `tiktoken` 누락](#3-tokenizer-초기화-실패--sentencepiece--tiktoken-누락)
4. [pip 미인식으로 인한 Accelerate 설치 실패](#4-pip-미인식으로-인한-accelerate-설치-실패)
5. [CUDA Out of Memory (OOM)](#5-cuda-out-of-memory-oom)
6. [모델 경로 없음 — `model path not found`](#6-모델-경로-없음--model-path-not-found)
7. [entrypoint 사용 불가 — manifest 생성 실패](#7-entrypoint-사용-불가--manifest-생성-실패)
8. [torch packing 실패 — `--no-deps` + `requirements.txt` 분리로 해결](#8-torch-packing-실패----no-deps--requirementstxt-분리로-해결)
9. [`@Endpoint` 함수 직접 호출 및 스키마 미인식](#9-endpoint-함수-직접-호출-및-스키마-미인식)

---

## 1. Flash 패키징(pack) 누락 — `flash_manifest.json not found`

### 증상

```bash
FileNotFoundError: flash_manifest.json not found
Endpoint deploy failed
```

Endpoint 배포 직후 Worker가 기동되지 않고 즉시 실패 상태로 전환된다.

### 재현 조건

- `runpod flash deploy` 를 `runpod flash build` 없이 직접 실행한 경우
- 코드를 수정한 뒤 build 단계를 생략하고 재배포한 경우
- CI/CD 파이프라인에서 build 스텝이 누락된 경우

### 원인

RunPod Flash는 **코드 → 바로 실행** 구조가 아니다.  
`deploy` 명령은 이미 패키징된 `flash_manifest.json` 을 참조하며, 해당 파일은 반드시 `build` 단계에서 생성된다.

```text
[코드 작성] → [runpod flash build] → flash_manifest.json 생성
                                            ↓
                               [runpod flash deploy] → Endpoint 등록
```

### 해결 절차

```bash
# 1. 프로젝트 루트에서 build 실행
runpod flash build

# 2. build 성공 여부 확인 (flash_manifest.json 존재 확인)
ls -la flash_manifest.json

# 3. 정상 확인 후 deploy
runpod flash deploy
```

### 예방

- CI/CD 파이프라인에 `build → deploy` 순서를 명시적으로 정의한다.
- 코드 변경 시 항상 build를 선행 실행한다.

---

## 2. 401 Unauthorized

### 증상

```
HTTP 401 Unauthorized
{"error": "Unauthorized"}
```

FastAPI → RunPod Serverless API 호출 시 응답으로 401이 반환된다.

### 재현 조건

- `RUNPOD_API_KEY` 환경변수가 설정되지 않은 경우
- API Key가 만료되었거나 잘못된 값이 주입된 경우
- Docker Compose 환경에서 `.env` 파일이 로드되지 않은 경우

### 원인

RunPod API는 모든 요청의 `Authorization: Bearer <API_KEY>` 헤더를 검증한다.  
키가 없거나 유효하지 않으면 요청 자체가 인증 단계에서 거부된다.

### 해결 절차

```bash
# 1. 환경변수 주입 여부 확인
echo $RUNPOD_API_KEY

# 2. .env 파일에 키 존재 여부 확인
grep RUNPOD_API_KEY .env

# 3. RunPod 콘솔에서 API Key 유효성 확인
#    https://www.runpod.io/console/user/settings → API Keys

# 4. Docker Compose 기동 시 env_file 설정 확인
# docker-compose.yml 내 backend 서비스에 아래 항목 존재 여부 확인:
#   env_file:
#     - .env
```

### 예방

- `.env.example` 에 `RUNPOD_API_KEY=` 항목을 명시하고, 신규 팀원 온보딩 체크리스트에 포함한다.
- 키 로테이션 시 Docker 컨테이너를 재기동한다.

---

## 3. Tokenizer 초기화 실패 — `sentencepiece` / `tiktoken` 누락

### 증상

```
LookupError: sentencepiece is required but not installed.
ImportError: No module named 'tiktoken'
```

Worker 기동 후 모델 로딩 단계에서 오류가 발생한다.

### 재현 조건

- `requirements.txt` 에 `sentencepiece` 또는 `tiktoken` 이 누락된 경우
- `transformers` 만 명시하고 보조 패키지를 생략한 경우

### 원인

EXAONE 계열 모델의 tokenizer는 `sentencepiece` 를 내부적으로 사용한다.  
`transformers` 패키지는 이를 선택적 의존성으로 처리하기 때문에 자동 설치되지 않는다.

### 해결 절차

`requirements.txt` 에 패키지를 추가한다.  
(`torch` 는 RunPod 기본 이미지에 사전 설치되어 있으므로 제외)

```
transformers
accelerate
sentencepiece   # ← 추가
tiktoken        # ← 추가 (필요 시)
```

변경 후 **build → deploy** 를 재실행한다.

```bash
runpod flash build && runpod flash deploy --no-deps
```

---

## 4. pip 미인식으로 인한 Accelerate 설치 실패

### 증상

```
ImportError: Using `low_cpu_mem_usage=True` or a `device_map` requires Accelerate: `pip install accelerate`
```

`dependencies` 에 `accelerate` 를 명시했음에도 Worker 기동 시 위 오류가 발생한다.

### 재현 조건

- `@Endpoint` 의 `dependencies` 에만 `accelerate` 를 추가하고 `requirements.txt` 를 별도로 제공하지 않은 경우
- `device_map="auto"` 옵션을 사용하는 경우

### 원인

RunPod Serverless 플랫폼에서 `pip` 가 정상적으로 동작하지 않아  
`@Endpoint` 의 `dependencies` 에 명시한 패키지가 실제로 설치되지 않는다.  
이는 RunPod 플랫폼 자체의 이슈로, `dependencies` 방식으로는 직접 해결이 불가능하다.

```
pip 미인식 (RunPod 플랫폼 이슈)
    ↓
dependencies의 accelerate 설치 실패
    ↓
device_map="auto" 사용 불가
```

### 해결 절차

`dependencies` 대신 `requirements.txt` + `--no-deps` 방식으로 전환한다.  
`requirements.txt` 는 Worker 기동 시 런타임에서 별도로 설치되므로 pip 미인식 문제를 우회할 수 있다.

```
# requirements.txt
transformers
accelerate     # ← 여기서 설치
sentencepiece
```

```bash
runpod flash deploy --no-deps
```

이후 `device_map="auto"` 정상 동작 확인됨.

> **참고:** `@Endpoint` 의 `dependencies` 는 pip 미인식 이슈로 신뢰할 수 없다.  
> 모든 패키지는 `requirements.txt` 로 관리한다.

---

## 5. CUDA Out of Memory (OOM)

### 증상

```
torch.cuda.OutOfMemoryError: CUDA out of memory.
Tried to allocate X GiB (GPU 0; 47.50 GiB total capacity; ...)
```

추론 요청 처리 중 Worker가 크래시된다.

### 재현 조건

- `max_new_tokens` 를 과도하게 크게 설정한 경우 (예: 4096 이상)
- 입력 `messages` 의 누적 토큰 수가 매우 긴 경우
- 동시 요청이 발생하여 배치 처리 시 메모리가 초과된 경우

### 원인

GPU VRAM(48GB) 대비 모델 가중치(약 16GB) + KV Cache + 활성화 메모리의 합이 한계를 초과한다.  
특히 `max_new_tokens` 가 클수록 KV Cache 사용량이 선형적으로 증가한다.

### 해결 절차

**① max_new_tokens 제한**

```python
# 추론 로직에서 상한 강제 적용
max_new_tokens = min(input_data.get("max_new_tokens", 512), 1024)
```

**② 추론 후 메모리 해제**

```python
import gc
import torch

def handler(job):
    try:
        result = model.generate(...)
        return {"ok": True, "text": result}
    finally:
        gc.collect()
        torch.cuda.empty_cache()
```

**③ 입력 길이 제한 (FastAPI 측)**

```python
# services 레이어에서 메시지 토큰 수 사전 검증
MAX_INPUT_TOKENS = 2048
```

### 예방

- `workers` 를 `(1, 1)` 로 고정하여 동시 요청을 방지한다.
- 운영 환경에서 `max_new_tokens` 기본값을 512 이하로 설정한다.

### 추후 대응

`AirLLM` 패키지처럼 쪼개서 연산하는 방식으로 전환 검토.

---

## 6. 모델 경로 없음 — `model path not found`

### 증상

```
OSError: [model_name] does not appear to have a file named config.json.
ValueError: /runpod-volume/models/... is not a valid model directory.
```

Worker 최초 기동 또는 콜드 스타트 시 모델 로딩에 실패한다.

### 재현 조건

- Network Volume이 Endpoint에 마운트되지 않은 경우
- Volume 내 모델 파일이 다운로드되지 않은 경우
- 모델 경로 상수가 실제 Volume 마운트 경로와 불일치하는 경우

### 원인

RunPod Serverless Worker에서 Network Volume은 `/runpod-volume` 에 마운트된다.  
이 경로와 코드 내 모델 경로 상수가 일치하지 않으면 파일을 찾지 못한다.

### 해결 절차

**① 마운트 경로 확인**

```python
# handler 내 디버그 코드 (임시)
import os
print(os.listdir("/runpod-volume"))
print(os.listdir("/runpod-volume/models"))
```

**② 모델 경로 상수 수정**

```python
# 올바른 경로 예시
MODEL_PATH = "/runpod-volume/exaone-3.5-7.8b"
```

**③ Endpoint 설정에서 Volume 마운트 확인**

```python
@Endpoint(
    name="exaone",
    gpu=RUNPOD_GPU,
    volume=get_runpod_volume(),   # ← Volume 객체 연결 여부 확인
    ...
)
```

**④ Volume 내 모델 파일 존재 여부 확인**

RunPod 콘솔 → Storage → 해당 Volume 선택 → File Browser에서 모델 디렉토리 및 `config.json` 존재 여부를 직접 확인한다.

### 예방

- 모델 경로를 환경변수 또는 설정 상수로 단일 관리한다.
- Volume 마운트 경로는 `/runpod-volume` 으로 고정하고 코드 전반에 하드코딩을 금지한다.

---

## 7. entrypoint 사용 불가 — manifest 생성 실패

### 증상

```
Error: entrypoint is not supported in RunPod Flash
flash_manifest.json could not be generated
```

`runpod flash build` 실행 시 manifest가 생성되지 않고 빌드가 중단된다.

### 재현 조건

- `Dockerfile` 또는 Endpoint 설정에 `ENTRYPOINT` / `CMD` 를 직접 지정한 경우
- `Endpoint(image=...)` 방식으로 커스텀 이미지를 사용하려 한 경우
- Flash가 아닌 일반 Serverless 방식의 설정을 Flash 프로젝트에 혼용한 경우

### 원인

RunPod Flash는 **decorator 기반 핸들러**를 자체 런타임으로 감싸는 구조다.  
`entrypoint` 를 직접 지정하면 Flash 런타임이 핸들러 진입점을 찾지 못해 manifest 자체를 생성할 수 없다.

```text
# Flash 내부 동작 구조
@Endpoint(...)       ← Flash가 이 decorator를 파싱하여 manifest 생성
async def handler(...):
    ...

# entrypoint 직접 지정 → Flash가 핸들러를 인식 불가 → manifest 생성 실패
```

### 해결 절차

```python
# ❌ 잘못된 방식 — entrypoint 직접 지정
# Dockerfile: ENTRYPOINT ["python", "handler.py"]
# Endpoint(image="my-image:latest", ...)

# ✅ 올바른 방식 — decorator만 사용
from runpod_flash import Endpoint

@Endpoint(
    name="exaone",
    gpu=RUNPOD_GPU,
    ...
)
async def exaone_infer(...):
    ...
```

1. `Dockerfile` 에서 `ENTRYPOINT` / `CMD` 제거
2. `Endpoint(image=...)` 방식을 `@Endpoint(...)` decorator 방식으로 전환
3. `runpod flash build` 재실행하여 manifest 생성 확인

### 예방

- Flash 프로젝트에서는 `entrypoint` 관련 설정을 일절 사용하지 않는다.
- `@Endpoint` decorator가 있는 파일 하나를 단일 진입점으로 유지한다.
- `flash run` 에서 생성이 안 되는 경우가 있으므로 `flash deploy` 로 확인한다.

---

## 8. torch packing 실패 — `--no-deps` + `requirements.txt` 분리로 해결

### 증상

```
PackagingError: Failed to pack dependency: torch
Error: torch wheel exceeds size limit / incompatible platform tag
Deploy blocked: required dependency missing
```

`runpod flash build` 에서 `torch` packing이 실패하며, `--no-deps` 옵션만으로는 deploy 단계에서 차단된다.

### 재현 조건

- `dependencies` 에 `torch` 를 직접 포함한 경우
- Flash packing이 torch wheel을 번들링하려 시도하는 경우
- CPU 전용 torch wheel 또는 플랫폼 불일치 wheel을 사용하는 경우

### 원인

`torch` 는 패키지 크기가 매우 크고(~2GB) 플랫폼(CUDA 버전)에 종속적이다.  
Flash의 packing 단계는 wheel을 번들링하는 방식인데, torch는 크기 제한 또는 플랫폼 태그 불일치로 실패한다.  
`--no-deps` 단독으로는 deploy 시 런타임 의존성 검증에서 여전히 차단된다.

### 해결 절차

`--no-deps` 옵션과 함께 `requirements.txt` 를 분리하여 제공한다.  
Flash는 `requirements.txt` 를 Worker 기동 시 런타임에서 별도로 설치하므로, packing 단계를 우회할 수 있다.

**① `requirements.txt` 작성**

```
transformers
accelerate
sentencepiece
# torch는 RunPod 기본 이미지에 사전 설치되어 있으므로 제외
```

**② `--no-deps` 옵션으로 deploy**

```bash
runpod flash deploy --no-deps
```

**③ `@Endpoint` `dependencies` 비워두기**

```python
@Endpoint(
    name="exaone",
    gpu=RUNPOD_GPU,
    # dependencies 생략 — requirements.txt 로 대체
)
```

### 예방

- `torch` 는 `dependencies` 와 `requirements.txt` 모두에서 제외한다.
- `--no-deps` + `requirements.txt` 분리 방식을 표준 배포 절차로 고정한다.
- RunPod 공식 문서의 `flash` 섹션을 참조하여 serverless를 준비한다.

---

## 9. `@Endpoint` 함수 직접 호출 및 스키마 미인식

### 증상

```
# FastAPI에서 직접 호출 시
TypeError: 'Endpoint' object is not callable
# 또는 스키마 관련 오류
ModuleNotFoundError: No module named 'pydantic'
PackagingWarning: pydantic not resolved during pack
```

FastAPI에서 `@Endpoint` 데코레이터가 붙은 함수를 직접 import해서 호출하면 오류가 발생한다.  
또한 `dependencies` 에 `pydantic` 을 명시했음에도 packing 후 스키마 인식에 실패한다.

### 재현 조건

- FastAPI 서비스 레이어에서 `exaone_infer(payload)` 형태로 직접 호출한 경우
- `@Endpoint` 데코레이터 함수를 일반 Python 함수처럼 import한 경우
- `dependencies` 에 `"pydantic"` 을 버전 미지정으로 추가한 경우
- Pydantic v1 / v2 혼용 환경에서 빌드한 경우

### 원인

`@Endpoint` 데코레이터가 붙은 함수는 RunPod 런타임용으로 래핑된 객체다.  
FastAPI에서 직접 호출하면 래핑된 객체를 함수처럼 실행하려 해서 오류가 발생한다.  
FastAPI는 반드시 **RunPod API를 HTTP로 호출**하는 방식으로만 연동해야 한다.

Pydantic 미인식은 Flash packing이 버전 미지정 패키지를 최신 버전으로 해석하는 과정에서  
v1/v2 호환 충돌이 발생하거나, 내부 패키지로 분류되어 packing 대상에서 자동 제외되어 발생한다.  
근본적으로는 handler 내부에서 Pydantic을 사용하는 것 자체가 Flash 환경에서 불안정하다.

### 해결 절차

**① FastAPI → RunPod HTTP 호출로 전환**

```python
# ❌ 직접 호출 — @Endpoint 래핑으로 동작 안 함
from llm.exaone import exaone_infer
result = await exaone_infer(payload)

# ✅ RunPod API HTTP 호출
import httpx

result = await httpx.AsyncClient().post(
    f"https://api.runpod.ai/v2/{ENDPOINT_ID}/runsync",
    headers={"Authorization": f"Bearer {RUNPOD_API_KEY}"},
    json={"input": payload},
)
```

**② handler 내부 응답 스키마를 TypedDict로 전환 (Pydantic 제거) — 해결됨**

```python
# ✅ ExaoneResponse — TypedDict 사용으로 정상 동작
from typing import TypedDict

class ExaoneResponse(TypedDict, total=False):
    ok: bool
    text: str
    error: str
```

**③ handler 입력 스키마 — 미해결**

`ExaoneRequest` (입력 스키마) 를 TypedDict로 정의해도 RunPod Flash가 매개변수를 인식하지 못한다.  
현재 아래와 같이 `input: dict = None, **kwargs` 방식으로 우회하여 동작 중이나 근본 해결은 아니다.

```python
# 현재 우회 방식 — 입력 스키마 미인식으로 인한 임시 방편
async def exaone_infer(input: dict = None, **kwargs) -> ExaoneResponse:
    if input is None:
        input = {}
    input.update(kwargs)
    data: ExaoneRequest = {"input": input}
    ...
```

> **상태:** 입력 스키마(`ExaoneRequest`) RunPod 미인식 — **미해결**

### 예방

- `@Endpoint` 함수는 절대 FastAPI에서 직접 import하여 호출하지 않는다.
- Flash handler 응답은 `TypedDict` 로 정의한다.
- 입력 스키마는 해결 방법 확인 전까지 `input: dict = None, **kwargs` 방식을 사용한다.

---

## 핵심 체크리스트 (배포 전 확인)

| 항목 | 확인 방법 |
|------|----------|
| `@Endpoint` decorator 사용 | `Endpoint(image=...)` 또는 `entrypoint` 방식 미사용 여부 확인 |
| `runpod flash build` 선행 실행 | `flash_manifest.json` 존재 확인 |
| `function_name` 포함 | API 호출 payload에 `function_name` 키 존재 여부 확인 |
| `requirements.txt` 완전성 | `transformers`, `accelerate`, `sentencepiece` 포함 여부 (`torch` 제외) |
| `torch` 미명시 | `requirements.txt` 에 `torch` 없는지 확인 (기본 이미지 사용) |
| `--no-deps` 배포 | `runpod flash deploy --no-deps` 사용 여부 확인 |
| `@Endpoint` 직접 호출 금지 | FastAPI에서 HTTP 호출 방식 사용 여부 확인 |
| handler 응답 스키마 TypedDict 사용 | Pydantic 대신 `TypedDict` 사용 여부 확인 |
| `RUNPOD_API_KEY` 환경변수 | `echo $RUNPOD_API_KEY` 또는 `.env` 확인 |
| 모델 경로 일치 | 코드 상수 vs Volume 실제 경로 일치 여부 |
| Volume 마운트 | Endpoint 설정에 `volume=` 연결 여부 |
