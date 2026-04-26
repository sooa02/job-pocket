# 🔄 Job-Pocket RAG 파이프라인

> **문서 목적**: Job-Pocket의 모듈화된 RAG(Retrieval-Augmented Generation) 프로세스와 성능 최적화 전략을 기술한다.
> **최종 수정일**: 2026-04-26
> **버전**: v0.3.0 (Modularized & Optimized)

---

## 1. 파이프라인 아키텍처 개요

Job-Pocket은 단순한 검색-생성을 넘어, 결과물의 완성도를 극대화하기 위해 **오케스트레이터(`chat_logic`) 중심의 다단계 분기 파이프라인**을 사용합니다.

### 1.1 핵심 설계 원칙
- **Separation of Concerns**: 파싱, 생성, 평가 로직을 독립된 모듈로 분리하여 관리합니다.
- **Data Persistence & Reuse**: 첫 단계에서 구조화된 사용자 요청(`ParsedUserRequest`)을 이후 모든 단계에서 재사용하여 연산 낭비를 최소화합니다.
- **Search Hoisting**: 품질 미달로 인한 재생성 루프 시, 동일한 검색 결과를 재사용하여 지연 시간과 API 비용을 절감합니다.

---

## 2. 전체 흐름도 (Optimized Flow)
![자소서 생성 파이프라인](../assets/images/model/rag_pipeline.png)

---

## 3. 단계별 상세 설명

### 3.1 Step 1: Parse (요청 구조화)
사용자의 자연어 메시지를 `ParsedUserRequest` Pydantic 객체로 변환합니다.
- **하이브리드 파싱**: 정규표현식(Regex)으로 명확한 정보를 먼저 추출하고, 부족한 정보는 LLM(`JsonOutputParser`)이 채우는 방식입니다.
- **결과 활용**: 추출된 `company`, `job`, `question_type` 등은 이후 모든 단계에서 프롬프트의 핵심 컨텍스트로 주입됩니다.

### 3.2 Step 2: Draft (RAG 기반 초안 생성)
가장 높은 리소스를 소모하는 단계로, 검색과 생성이 결합됩니다.
- **Retrieval (Hoisted)**: `RetrievalService`를 통해 FAISS 인덱스와 MySQL에서 유사한 스펙을 가진 이전 지원자의 데이터를 유사도 순서대로 3개 가져옵니다. 
- **Generator (EXAONE 3.5)**: RunPod Serverless 엔드포인트를 호출하여 한국어 문맥에 최적화된 초안을 작성합니다.
- **Quality Loop**: 생성 후 `Evaluator`가 점수를 측정합니다. 품질 미달 시 **검색을 다시 수행하지 않고**, 이전 실패 사유만 프롬프트에 추가하여 재생성합니다.

### 3.3 Step 3~4: Refine & Fit (고도화 및 보정)
- **Refine**: EXAONE의 거친 표현을 GPT-4o-mini를 통해 매끄럽고 설득력 있는 문체로 다듬습니다.
- **Fit**: 사용자가 요청한 글자 수 제한(`char_limit`)에 맞게 문장을 압축하거나 보충합니다.

### 3.4 Step 5: Final (평가 및 조립)
- **Evaluator**: 완성된 자소서를 7가지 관점에서 평가하여 '좋다/보통/아쉬움' 등급과 구체적인 **보완 포인트**를 생성합니다.
- **Final Assembly**: 본문과 평가 결과를 마크다운 형식으로 결합하여 사용자에게 최종 응답을 반환합니다.

---

## 4. 성능 및 비용 최적화 전략

| 기술적 해법 | 설명 | 기대 효과 |
|:--- |:--- |:--- |
| **Search Hoisting** | 검색 결과를 재생성 루프 밖에서 1회만 수행 | API 호출 66% 절감, Latency 단축 |
| **Pydantic Bridge** | 전 단계의 분석 결과를 객체 형태로 공유 | 백엔드 내 중복 파싱 연산 제거 |
| **Async Polling** | RunPod 비동기 호출 시 완료 시점만 체크 | 서버 리소스 효율화 및 안정적 응답 보장 |
| **Prompt Caching** | 공통 시스템 페르소나를 상수화하여 관리 | 프롬프트 토큰 관리 용이성 |

> 해당 전략의 자세한 내용은 [chat logic 최적화](../troubles/chat_logic_optimize.md)를 참고해주세요.
---

## 5. 관련 파일 및 모듈

- **오케스트레이터**: `backend/services/chat_logic.py`
- **유사 사례 검색**: `backend/services/retrieval_service.py`
- **구조화 파싱**: `backend/services/chat/parser.py`
- **초안 생성**: `backend/services/chat/generator.py`
- **품질 평가**: `backend/services/chat/evaluator.py`

---
*last updated: 2026-04-26 | 조라에몽 팀*
