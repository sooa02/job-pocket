# 🧬 Job-Pocket 임베딩 모델 (Qwen3-Embedding-0.6B)

> **문서 목적**: Job-Pocket이 채택한 임베딩 모델의 특성, 선정 이유, 설정 옵션, 사용 방식을 기술한다.
> **작성일**: 2026-04-22
> **버전**: v0.2.0
> **관련 파일**: `backend/services/chat_logic.py` (68~72줄), `backend/retriever.py`

---

## 1. 모델 개요

### 1.1 기본 정보

| 항목 | 값 |
|---|---|
| 모델명 | `Qwen/Qwen3-Embedding-0.6B` |
| 제공 | Alibaba Cloud (Qwen 시리즈) |
| 파라미터 수 | 0.6B (600M) |
| 출력 차원 | 1024 |
| 컨텍스트 길이 | 8,192 tokens |
| 모델 크기 | ~1.2GB (FP32) |
| 라이선스 | Apache 2.0 |
| 발표 | 2024년 말 |

### 1.2 역할

HybridRetriever에서 사용자 쿼리와 자소서 본문을 1024차원 벡터로 변환한다. 이 벡터는 FAISS 인덱스에서 유사도 검색의 기반이 된다. MySQL의 `resume_vectors` 테이블에 적재될 벡터도 동일 모델로 생성된다.

---

## 2. 선정 이유

### 2.1 한국어 성능

Qwen3-Embedding은 중국어 중심 모델이지만 다국어 학습 데이터 비중이 상당하며, 한국어 처리 품질이 평균 이상이다. MTEB 벤치마크의 한국어 retrieval 태스크에서 경쟁 모델 대비 상위권 성능을 보이는 것으로 보고되었다. Job-Pocket의 검색 대상은 한국어 자소서이므로 한국어 성능이 1차 선정 기준이다.

### 2.2 경량성

0.6B 파라미터는 CPU 추론에 적합한 크기다. 대형 임베딩 모델(1.5B 이상)은 GPU가 필요하거나 CPU 추론 시 지연이 크다. Job-Pocket의 Backend 컨테이너는 GPU 없이 CPU만으로 운영되므로, 모델 크기는 실용적 제약이다.

### 2.3 1024차원의 적절성

차원 수는 검색 품질과 저장/연산 비용의 트레이드오프다. 실험적으로 1024차원은 한국어 단락 수준 텍스트 유사도 검색에서 "diminishing returns"가 시작되는 지점이다. 1536차원 이상은 품질 이득이 작은 반면 FAISS 인덱스 크기와 임베딩 계산 시간이 선형 증가한다.

### 2.4 Apache 2.0 라이선스

상업 사용·재배포·파생 저작물 모두 허용된다. 자체 배포 환경에 제약이 없으며, 미래의 파인튜닝 옵션도 열려 있다.

### 2.5 대안 비교

| 모델 | 차원 | 크기 | 한국어 품질 | CPU 추론 | 라이선스 |
|---|---|---|---|---|---|
| **Qwen3-Embedding-0.6B (선택)** | 1024 | 1.2GB | 우수 | 양호 | Apache 2.0 |
| BGE-M3 | 1024 | 2.3GB | 우수 | 느림 | MIT |
| KoSimCSE-roberta | 768 | 420MB | 매우 우수 | 빠름 | Apache 2.0 |
| ko-sroberta-multitask | 768 | 430MB | 우수 | 빠름 | Apache 2.0 |
| text-embedding-3-small (OpenAI) | 1536 | API | 우수 | — | 유료 |
| multilingual-e5-large | 1024 | 2.2GB | 양호 | 느림 | MIT |
| Upstage solar-embedding-1-large | 4096 | API | 매우 우수 | — | 유료 |

**KoSimCSE 대신 Qwen3를 택한 이유**: KoSimCSE는 한국어 성능이 최상위지만 컨텍스트 길이가 짧다(512 tokens). 자소서는 1~2천자 분량이라 긴 컨텍스트를 한 번에 처리 가능한 Qwen3(8192 tokens)가 더 적합하다.

**BGE-M3 대신 Qwen3를 택한 이유**: BGE-M3는 한국어 품질이 비슷하지만 크기가 거의 2배다. 경량성을 우선시했다.

---

## 3. 설정

### 3.1 LangChain을 통한 로드

```python
from langchain_huggingface import HuggingFaceEmbeddings

hf_embeddings = HuggingFaceEmbeddings(
    model_name="Qwen/Qwen3-Embedding-0.6B",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)
```

이 한 번의 초기화로 `chat_logic.py` 모듈 로드 시점에 모델이 다운로드·로드된다. 최초 실행 시 HuggingFace Hub에서 약 1.2GB를 다운로드하여 `~/.cache/huggingface/hub/`에 캐싱한다.

### 3.2 옵션 설명

**`device='cpu'`**: CPU에서 PyTorch 추론을 실행한다. GPU가 있는 환경에서는 `'cuda'`로 바꿀 수 있으나, 0.6B 모델은 CPU로도 충분히 빠르다.

**`normalize_embeddings=True`**: 출력 벡터의 L2 norm을 1로 정규화한다. 이로 인해 FAISS의 기본 L2 distance 계산이 cosine similarity와 동일한 순위를 매기게 된다. 정규화 여부는 검색 품질에 직접 영향을 주므로 활성화가 필수다.

### 3.3 컨테이너 내 캐싱

v0.2.0에서는 모델 파일이 컨테이너 재시작 시마다 재다운로드될 수 있다. `~/.cache/huggingface/`를 볼륨 마운트하여 영속화하는 설정을 v0.3.0에서 추가할 예정이다:

```yaml
# docker-compose.yaml 개선안
backend:
  volumes:
    - ./backend:/app
    - huggingface_cache:/root/.cache/huggingface

volumes:
  huggingface_cache:
```

---

## 4. 사용 패턴

### 4.1 쿼리 임베딩

HybridRetriever 내부에서 쿼리 문자열을 임베딩한다. 직접 호출하지 않고 LangChain의 `FAISS.similarity_search_with_score`가 내부적으로 호출한다:

```python
# retriever.py 내부 동작
query = "[최종학력] ○○대 컴퓨터공학 [경력] ABC 인턴 [기술] Python, SQL"
docs_and_scores = self.vectorstore.similarity_search_with_score(
    query=query,   # → embed_query(query) 자동 호출
    k=50
)
```

### 4.2 인덱스 구축 시 임베딩

FAISS 인덱스 빌드 스크립트(v0.3.0 예정)에서 자소서 본문을 임베딩한다:

```python
# scripts/embed/build_faiss_index.py (예시)
texts_to_embed = [row['selfintro'] for row in rows]
vectorstore = FAISS.from_texts(
    texts=texts_to_embed,
    embedding=hf_embeddings,
    metadatas=[{...}],
    ids=[str(row['id']) for row in rows]
)
```

### 4.3 쿼리 구성 전략

쿼리는 사용자의 이력 정보로 구성한다. 단순 키워드 나열보다 구조화된 형식이 임베딩 품질에 유리하다:

```python
query = f"""[최종학력] {profile['school']} {profile['major']}
[경력 및 경험]
{profile['exp']}
{profile['awards']}
[기술 및 역량]
{profile['tech']}
"""
```

대괄호 섹션 헤더가 있는 이 형식은 자소서 샘플의 구조와 유사하여, 자소서 본문과의 유사도가 높게 계산된다.

---

## 5. 쿼리 vs 문서 임베딩의 비대칭

일부 임베딩 모델은 쿼리와 문서를 다르게 처리한다(예: `query: `, `passage: ` prefix). Qwen3-Embedding은 이런 비대칭 처리를 권장하지만, v0.2.0에서는 단순화를 위해 prefix 없이 사용하고 있다.

v0.3.0에서 다음 전략 도입을 검토한다:

```python
# 인덱스 빌드 시
text_to_embed = f"passage: {selfintro_text}"

# 쿼리 시
query_to_embed = f"query: {user_query}"
```

실험에서 retrieval 품질이 5~10% 개선된다는 결과가 보고되어 있다. 구현 비용이 낮아 v0.3.0에 포함될 가능성이 높다.

---

## 6. 성능 특성

### 6.1 추론 속도

| 하드웨어 | 단일 쿼리 임베딩 시간 |
|---|---|
| Intel Xeon 4코어 | 0.5~1.0초 |
| Apple M1 8코어 | 0.3~0.6초 |
| NVIDIA T4 GPU | 0.05~0.1초 |

Job-Pocket의 Backend는 CPU 환경을 기준으로 설계되므로 1초 내외의 지연이 예상된다. Draft 단계의 LLM 추론 지연(수 초~수십 초)에 비하면 임베딩 지연은 전체 파이프라인에서 지배적 요소가 아니다.

### 6.2 메모리 사용량

| 항목 | 크기 |
|---|---|
| 모델 가중치 (FP32) | ~1.2GB |
| 모델 가중치 (FP16) | ~600MB |
| 추론 시 피크 메모리 | ~1.5GB (긴 문서 처리 시) |

Backend 컨테이너의 기본 메모리 한도(2GB) 내에서 안정적으로 운영 가능하다.

### 6.3 배치 처리

LangChain의 `HuggingFaceEmbeddings`는 내부적으로 배치 처리를 지원한다. 인덱스 빌드 같은 대량 임베딩 시 `encode_kwargs={'batch_size': 32}`로 조정 가능하다. 단일 쿼리 런타임에는 해당하지 않는다.

---

## 7. 정규화의 수학적 의미

### 7.1 정규화 없이 L2 distance

임베딩이 정규화되지 않은 경우, L2 distance는 벡터의 크기에도 영향을 받는다:

```
L2(a, b) = ||a - b||₂
```

텍스트 길이가 긴 문서의 벡터는 norm이 크게 나올 수 있어, 유사도 순위가 왜곡될 수 있다.

### 7.2 정규화 후 L2 distance = cosine similarity

정규화된 벡터(||a|| = ||b|| = 1)에서 다음 관계가 성립한다:

```
L2(a, b)² = 2 - 2·cos(a, b)
```

즉 L2 distance의 순위는 cosine similarity의 순위와 **정확히 반대**가 된다. 가까울수록 유사한 정답이 된다. 한국어 의미 유사도 검색에서는 cosine이 L2보다 안정적이라는 것이 경험적으로 확인된 사실이다.

### 7.3 FAISS 인덱스 타입과의 관계

FAISS의 `IndexFlatL2`는 L2 distance를 사용한다. 정규화된 벡터를 넣으면 cosine similarity 순위와 동일해진다. 대안으로 `IndexFlatIP`(Inner Product)를 사용하면 정규화된 벡터에서 직접 cosine을 계산하지만, LangChain의 기본 FAISS 래퍼는 L2를 사용하므로 본 프로젝트는 L2 + 정규화 조합을 택한다.

---

## 8. 품질 검증 (향후)

### 8.1 평가 지표

v0.3.0에서 도입할 Retrieval 평가 지표:

| 지표 | 의미 | 목표값 |
|---|---|---|
| Recall@3 | 정답 문서가 상위 3개에 포함되는 비율 | ≥ 0.70 |
| Recall@10 | 정답 문서가 상위 10개에 포함되는 비율 | ≥ 0.90 |
| MRR (Mean Reciprocal Rank) | 정답 문서의 평균 역순위 | ≥ 0.50 |
| Diversity@3 | 상위 3개 문서의 다양성 | ≥ 0.60 |

### 8.2 골든 셋 구성

평가용 정답 셋 50건을 수동으로 구성한다. 각 항목은 다음과 같다:

- 쿼리: 이력 정보 텍스트
- 정답: 해당 쿼리에 유사하다고 판단한 자소서 ID 리스트

`evaluation/datasets/golden_qa.jsonl`로 저장되며, `evaluation/run_retrieval_eval.py`에서 평가를 실행한다.

### 8.3 A/B 테스트

향후 임베딩 모델 교체 검토 시, 같은 골든 셋으로 두 모델을 비교한다. 지표 개선이 유의미해야 교체한다.

---

## 9. 관측 및 디버깅

### 9.1 임베딩 시각화

LangSmith 대시보드에서 각 쿼리의 검색 결과를 시각적으로 확인할 수 있다 (LangSmith 활성화 시). `@traceable` 데코레이터가 retriever에 주석 처리되어 있으며, v0.3.0에서 활성화 예정이다.

### 9.2 오프라인 시각화

개발 중 임베딩 품질 확인을 위해 T-SNE/UMAP 시각화 스크립트를 운영 편의상 준비할 수 있다:

```python
# scripts/evaluation/visualize_embeddings.py (예시)
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

vectors = np.array([emb for emb, _ in vectorstore.docstore._dict.values()])
tsne = TSNE(n_components=2, random_state=42).fit_transform(vectors)
plt.scatter(tsne[:, 0], tsne[:, 1], c=grades)
plt.savefig('embeddings.png')
```

이런 시각화는 비슷한 grade의 자소서가 벡터 공간에서 클러스터를 형성하는지 확인하는 용도로 활용한다.

---

## 10. 제약 및 향후 계획

### 10.1 현재 제약

**캐시 볼륨 미설정**: 컨테이너 재시작 시 모델 재다운로드 가능성.

**쿼리/문서 prefix 미사용**: Qwen3의 권장 사용 패턴 미적용.

**평가 지표 부재**: 검색 품질이 정량화되지 않아 개선 방향 판단이 어려움.

**FP32 로드**: FP16으로 전환하면 메모리 사용량 절반으로 감소 가능.

### 10.2 v0.3.0 개선

| 항목 | 내용 |
|---|---|
| 캐시 볼륨 | `huggingface_cache` volume 추가 |
| Prefix 전략 | `passage:`/`query:` 적용 실험 |
| 평가 스크립트 | `evaluation/run_retrieval_eval.py` |
| FP16 로드 | `model_kwargs={'torch_dtype': torch.float16}` |
| Peer-First 필터링 | grade 기반 재순위화 활성화 |

### 10.3 중장기 검토

**Multi-Vector 확장**: 자소서를 섹션별(지원동기/강점/포부)로 분리하여 각각 임베딩 → 섹션별 검색. 쿼리 유형별로 관련 섹션만 검색 가능.

**Reranking 도입**: 상위 K개를 가져온 뒤 cross-encoder(BGE-reranker 등)로 재순위화. 검색 품질 추가 향상.

**도메인 적응 파인튜닝**: 수집한 자소서 데이터로 contrastive learning을 통한 임베딩 모델 파인튜닝. 한국어 자소서 도메인에 더 특화된 벡터 생성.

---

## 11. 관련 문서

| 주제 | 문서 |
|---|---|
| Retriever 구현 | `docs/wiki/backend/rag_retriever.md` |
| RAG 파이프라인 | `docs/wiki/model/rag_pipeline.md` |
| 모델 선정 근거 | `docs/wiki/model/model_selection.md` |
| DB 설계 (VECTOR 컬럼) | `docs/wiki/backend/database.md` |

---

*last updated: 2026-04-22 | 조라에몽 팀*
