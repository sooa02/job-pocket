# Chat Logic 최적화 및 구조 개선 가이드

> **대상 서비스:** Job-Pocket 백엔드 생성 엔진 (`chat_logic`)  
> **런타임:** Python 3.12 (FastAPI)  
> **최초 작성일:** 2026-04-26  
> **작성자**: 이창우

---

## 목차

- [Chat Logic 최적화 및 구조 개선 가이드](#chat-logic-최적화-및-구조-개선-가이드)
  - [목차](#목차)
  - [1. 비대해진 단일 파일 구조 (God Object) — 유지보수 불능](#1-비대해진-단일-파일-구조-god-object--유지보수-불능)
    - [증상](#증상)
    - [재현 조건](#재현-조건)
    - [원인](#원인)
    - [해결 절차](#해결-절차)
    - [예방](#예방)
  - [2. 생성 루프 내 중복 연산 (검색/파싱) — Latency 및 비용 증가](#2-생성-루프-내-중복-연산-검색파싱--latency-및-비용-증가)
    - [증상](#증상-1)
    - [재현 조건](#재현-조건-1)
    - [원인](#원인-1)
    - [해결 절차](#해결-절차-1)
    - [예방](#예방-1)
  - [3. 불안정한 자연어 파싱 — 정규표현식(Regex)의 한계](#3-불안정한-자연어-파싱--정규표현식regex의-한계)
    - [증상](#증상-2)
    - [재현 조건](#재현-조건-2)
    - [원인](#원인-2)
    - [해결 절차](#해결-절차-2)
    - [예방](#예방-2)
  - [4. 비동기-동기 브릿징 실패 — RunPod Serverless 호출 대기 문제](#4-비동기-동기-브릿징-실패--runpod-serverless-호출-대기-문제)
    - [증상](#증상-3)
    - [재현 조건](#재현-조건-3)
    - [원인](#원인-3)
    - [해결 절차](#해결-절차-3)
    - [예방](#예방-3)

---

## 1. 비대해진 단일 파일 구조 (God Object) — 유지보수 불능

### 증상

- `chat_logic.py` 파일 하나가 1,000줄을 초과함.
- 프롬프트 수정 시 텍스트 정제 로직이나 DB 처리 로직을 건드리게 되어 사이드 이펙트 빈번 발생.
- 특정 단계(예: 평가)만 테스트하기가 매우 어려움.

### 재현 조건

- 모든 비즈니스 로직(파싱, 검색, 생성, 평가, 정제)을 단일 파일에 작성한 초기 개발 단계.
- 별도의 서비스/리포지토리 분리 없이 전역 함수로 기능을 추가해온 경우.

### 원인

초기 프로토타이핑 속도를 위해 `chat_logic.py`에 모든 기능을 집중시켰으나, 서비스가 고도화됨에 따라 관심사 분리(Separation of Concerns)가 이루어지지 않아 코드 가독성과 확장성이 저하됨.

### 해결 절차

**오케스트레이터 패턴**을 도입하여 파일 및 책임을 분리함.

- **`chat_logic.py`**: 각 단계를 호출하는 지휘자(Orchestrator) 역할만 수행.
- **`services/chat/`**: 세부 모듈로 분산.
    - `parser.py`: 요청 구조화 및 프로필 파싱.
    - `generator.py`: 초안 생성 로직.
    - `evaluator.py`: 품질 평가 및 최종 조립.
    - `analyzer.py`: 샘플 및 데이터 분석.

### 예방

- 단일 파일이 500줄을 넘어가기 시작하면 기능 단위로 모듈 분리를 검토한다.
- `@traceable` 데코레이터를 사용하여 단계별 실행을 모니터링한다.

---

## 2. 생성 루프 내 중복 연산 (검색/파싱) — Latency 및 비용 증가

### 증상

- 자소서 품질 미달로 인한 재생성 시, 전체 처리 시간이 기하급수적으로 증가.
- 불필요한 DB 조회 및 벡터 검색 로그가 반복적으로 찍힘.

### 재현 조건

- `regenerate_local_draft_if_needed` 함수 내부의 `for attempt in range(max_attempts):` 루프 안에서 검색(`retrieval`) 로직이 포함된 경우.

### 원인

이전 로직(`chat_logic.py.bak`)에서는 루프 내부에서 매번 사용자 프로필을 분석하고 유사 사례를 검색함. 이는 동일한 입력에 대해 동일한 검색 결과를 얻는 낭비임.

### 해결 절차

**루프 외부로 공통 연산을 이동(Hoisting)**하여 1회만 수행하고 결과를 재사용함.

```python
# 최적화된 로직
def regenerate_local_draft_if_needed(...):
    # 1. 루프 전 1회만 수행 (비용 절감)
    profile = chat_internal.parse_user_profile(user_profile)
    sample = chat_internal.get_sample_context(profile, retrieval_svc, active_llm)

    for attempt in range(max_attempts):
        # 2. 검색 결과(sample)를 재사용하여 생성만 수행
        draft = chat_internal.build_draft_with_exaone(parsed, profile, sample)
        ...
```

### 예방

- 루프 내부에서 외부 API나 DB 조회가 발생하는지 항상 체크한다.
- 변하지 않는 컨텍스트(사용자 프로필, 검색 샘플)는 미리 캐싱하거나 인자로 전달한다.

---

## 3. 불안정한 자연어 파싱 — 정규표현식(Regex)의 한계

### 증상

- 사용자가 "네이버 백엔드 지원해"라고 하면 회사명을 인식하지 못함.
- "500자 정도로 써줘"와 같은 구어체에서 글자 수 제한 파싱 실패.
- 잘못된 파싱으로 인해 엉뚱한 기업의 샘플을 검색해오는 현상.

### 재현 조건

- 정규표현식(`re.search`)만으로 회사, 직무, 문항 유형을 추출하려 할 때.

### 원인

정규표현식은 고정된 패턴 매칭에는 강하나, 사용자의 다양한 자연어 표현(Variations)을 모두 커버하기에는 유연성이 부족함.

### 해결 절차

**`JsonOutputParser`를 도입**하여 LLM에게 파싱 책임을 위임함.

```python
# parser.py 구현 예시
def llm_parse_user_request(user_message, active_llm):
    parser = JsonOutputParser(pydantic_object=LLMParsedRequest)
    prompt = ChatPromptTemplate.from_messages([
        ("system", PARSER_SYSTEM_PROMPT + "\n{format_instructions}"),
        ("human", "사용자 요청: {user_message}")
    ])
    chain = prompt | active_llm | parser
    return chain.invoke(...)
```

1. Pydantic 모델로 기대하는 JSON 스키마 정의.
2. `JsonOutputParser`를 통해 모델이 순수 JSON만 반환하도록 강제.
3. Regex 파싱 실패 시 LLM 파서를 사용하는 하이브리드 전략 적용.

### 예방

- 구조화되지 않은 복잡한 텍스트 분석은 정규표현식보다 LLM 파서를 우선 고려한다.

---

## 4. 비동기-동기 브릿징 실패 — RunPod Serverless 호출 대기 문제

### 증상

- EXAONE 초안 생성 요청 시 응답이 즉시 오지 않고 `job_id`만 반환됨.
- FastAPI 응답이 생성물 대신 RunPod의 작업 상태 JSON을 반환하는 현상.

### 재현 조건

- RunPod Serverless의 `/run` 엔드포인트를 호출하고 결과를 기다리지 않은 채 바로 리턴하는 경우.

### 원인

RunPod Serverless는 GPU 할당 및 추론 시간을 고려하여 비동기로 동작함. 사용자에게 최종 텍스트를 보여주려면 작업이 `COMPLETED` 상태가 될 때까지 기다리는(Polling) 과정이 필요함.

### 해결 절차

**Polling Loop와 Zero-wait Response 로직**을 적용함.

```python
# run_exaone.py
async def _call_exaone_async(...):
    # 1. Launch 요청
    res = await client.post(url_run, json=payload)
    launch_data = res.json()
    
    # 2. 즉시 완료 여부 확인 (Zero-wait)
    if launch_data.get("status") == "COMPLETED":
        return launch_data

    # 3. 미완료 시 완료될 때까지 폴링
    for attempt in range(150):
        await asyncio.sleep(2)
        status_res = await client.get(status_url)
        if status_res.json().get("status") == "COMPLETED":
            return status_res.json()
```

- `asyncio.run`을 통해 상위 서비스(동기)와 비동기 추론 로직을 연결함.
- 최초 요청에서 즉시 결과가 나올 경우 대기 없이 바로 반환하도록 최적화.

### 예방

- 외부 비동기 API 연동 시 상태 확인(Status Check) 로직이 포함되어 있는지 확인한다.
- 최대 대기 시간(Timeout)과 재시도 횟수를 명시적으로 정의한다.1