# vLLM 트러블슈팅 가이드

> **대상 서비스:** Job-Pocket LLM 추론 서버 (EXAONE-3.5-7.8B-Instruct-GGUF)  
> **런타임:** RunPod Serverless + RunPod Flash   
> **최초 작성일:** 2025-04-25  
> **작성자**: 조동휘

---

## 목차

1. [EXAONE-3.5-7.8B-Instruct vLLM 기동 실패 — 즉시 비활성화](#1-exaone-358b-instruct-vllm-기동-실패--즉시-비활성화)
2. [EXAONE-3.5-7.8B-Instruct-GGUF `/runsync` 호출 후 상태 변경](#2-exaone-358b-instruct-gguf-runsync-호출-후-상태-변경)

---

## 1. EXAONE-3.5-7.8B-Instruct vLLM 기동 실패 — 즉시 비활성화

### 증상

Worker 기동 직후 로그 출력 없이 즉시 `alert` 상태로 전환되며 비활성화된다.  
vLLM 서버가 실행조차 되지 않는다.

### 재현 조건

- `LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct` 모델을 vLLM에 올리는 경우
- RunPod Serverless Worker에서 vLLM으로 위 모델을 서빙하려는 경우

### 원인 (추정)

`LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct` 는 EXAONE 커스텀 아키텍처를 사용한다.  
vLLM은 지원하는 모델 아키텍처가 제한적이며, EXAONE 아키텍처가 미지원 목록에 해당할 가능성이 높다.  
이로 인해 vLLM이 모델을 로딩하기 전 아키텍처 검증 단계에서 실패하며, 로그 없이 즉시 종료되는 것으로 추정된다.

`LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-GGUF` 와의 차이점:
- **Instruct**: EXAONE 커스텀 아키텍처 → vLLM 미지원 추정
- **GGUF**: llama.cpp 기반으로 변환된 포맷 → 아키텍처 의존성이 낮아 호환 가능

### 상태

**미해결.** 원인 추정 단계이며 일단 우회적으로 LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-GGUF을 사용함

### 참고

- vLLM 지원 모델 목록: https://docs.vllm.ai/en/latest/models/supported_models.html

---

## 2. EXAONE-3.5-7.8B-Instruct-GGUF `/runsync` 호출 후 상태 변경

### 증상

- GPU 할당은 정상적으로 이루어짐
- `/runsync` 호출 후 몇 분 뒤 Worker 상태가 변경됨
- vLLM 서버가 정상적으로 health check를 통과하지 못함

### 재현 조건

- `LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct-GGUF` 모델을 vLLM으로 RunPod Serverless에 올리는 경우
- `/runsync` 엔드포인트로 추론 요청을 보내는 경우

### 원인

조사중

### 상태

**미해결.**