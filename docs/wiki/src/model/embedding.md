# 🧬 Job-Pocket 임베딩 모델 (Qwen3-Embedding-0.6B)

> **문서 목적**: Job-Pocket RAG 시스템의 핵심인 텍스트 벡터화 모델의 설정, 선정 이유 및 데이터 적재 시의 처리 전략을 기술한다.
> **최종 수정일**: 2026-04-26
> **버전**: v0.3.0 (Real-time Chunk Ingestion 반영)

---

## 1. 모델 개요 및 역할

Job-Pocket은 한국어 문맥 이해도가 높고 CPU 환경에서 효율적인 **Qwen3-Embedding-0.6B** 모델을 사용합니다.

- **사용 목적**: 
  - 사용자 쿼리(스펙 + 요청)의 벡터 변환.
  - 합격 자소서 데이터베이스 구축 시의 고차원(1024차원) 벡터 생성.
- **핵심 설정**: `normalize_embeddings=True`를 적용하여 FAISS의 `Inner Product` 연산이 코사인 유사도와 수학적으로 동일한하도록 보장합니다.

---

## 2. 데이터 인제스션 전략 (Real-time Chunking)

단순한 모델 로드를 넘어, 대량의 데이터를 안정적으로 임베딩하기 위해 `database/ingestion` 파이프라인과 연동된 최적화 기법을 사용합니다.

### 2.1 청크 단위 임베딩 (Chunk-based Embedding)
수만 건의 합격 자소서를 한 번에 임베딩할 경우 발생하는 메모리 부족(OOM) 문제를 해결하기 위해 **3,000건 단위의 청크(Chunk) 처리**를 수행합니다.
- `JobPocketPipeline` 내에서 실시간으로 `embed_documents`를 호출하여 임베딩을 생성하고 즉시 DB에 기록합니다.

---

## 3. 기술적 사양 (Technical Specs)

| 항목 | 상세 내용 | 비고 |
|:--- |:--- |:--- |
| **Model ID** | `Qwen/Qwen3-Embedding-0.6B` | HuggingFace Hub 로드 |
| **Dimension** | 1024-dim | 고해상도 시맨틱 추출 |
| **Device** | CPU (default) | 백엔드 컨테이너 리소스 최적화 |
| **Normalization** | L2 Normalization | 코사인 유사도 확보 |
| **Max Length** | 8,192 tokens | 장문 자소서 처리 가능 |

---

## 4. 실제 구현 및 설정 (`config.py`)

백엔드 시스템은 다음 설정을 통해 임베딩 모델을 초기화합니다.

```python
EMBEDDING_CONFIG = {
    "model_name": "Qwen/Qwen3-Embedding-0.6B",
    "model_kwargs": {"device": "cpu"},
    "encode_kwargs": {"normalize_embeddings": True},
}
```

---

## 5. 성능

- **추론 속도**: 일반적인 사용자 쿼리 1건당 약 0.5~1.0초 내외 소요 (CPU 기준).

---
*last updated: 2026-04-26 | 조라에몽 팀*
