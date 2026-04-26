# 🔍 Job-Pocket HybridRetriever 상세

> **문서 목적**: `backend/retriever.py`에 구현된 `HybridRetriever`의 동작 원리, 설계 결정, 인덱스 구축 방법, 운영 고려사항을 기술한다.
> **작성일**: 2026-04-22
> **버전**: v0.2.0
> **관련 파일**: `backend/retriever.py`, `backend/services/chat_logic.py`

---

## 1. 배경

### 1.1 왜 Hybrid인가

순수 벡터 DB(Qdrant, Pinecone 등)는 고차원 임베딩 검색에 최적화되어 있으나, 메타데이터 관리·관계형 쿼리·대용량 본문 저장에는 한계가 있다. 반대로 RDBMS는 정합성·트랜잭션·대용량 텍스트 저장이 강점이지만 유사도 검색 성능은 전용 벡터 DB에 미치지 못한다.

Job-Pocket의 자소서 검색 요구사항은 두 가지 특성을 모두 요구한다. 하나는 **사용자 쿼리와 유사한 자소서를 빠르게 찾는** 벡터 검색이고, 다른 하나는 **선별된 자소서의 본문·평가·등급을 정확히 가져오는** 관계형 조회다. 이에 따라 두 시스템의 장점을 조합한 2단계 검색 구조를 채택했다.

### 1.2 대안 검토

| 선택지 | 장점 | 단점 |
|---|---|---|
| FAISS + MySQL (선택) | 빠른 벡터 검색 + 정합성 있는 본문 조회 | FAISS 인덱스 별도 빌드·배포 필요 |
| MySQL 9 VECTOR만 | 단일 DB, 운영 단순 | 대량 벡터 검색 시 FAISS 대비 느림 |
| Qdrant + MySQL | 전문 벡터 DB 성능 | 컨테이너·설정 복잡도 증가 |
| FAISS만 | 최고 속도 | 본문·메타데이터 저장 불편 |

v0.2.0은 첫 번째 선택지를 채택했다. 장기적으로는 MySQL 9 VECTOR만으로 통합하는 경로도 고려 중이며, 두 구현의 성능을 v0.3.0에서 비교 평가할 예정이다.

---

## 2. 아키텍처

### 2.1 2단계 검색 흐름

```mermaid
flowchart LR
    Q[쿼리 텍스트<br/>학력 + 경력 + 기술] --> E[Qwen3-Embedding<br/>1024-dim 벡터]
    E --> F[FAISS Index<br/>similarity_search<br/>k=50]
    F --> S[score_map 구성<br/>ID → score]
    S --> T[Top-N 선정<br/>n=3]
    T --> I[ID 추출]
    I --> M[MySQL<br/>SELECT selfintro]
    M --> D[Document 조립<br/>본문 + 메타데이터]
    D --> R[List Document]
```

### 2.2 2단계로 나누는 이유

FAISS에는 임베딩 벡터와 ID만 저장하고, 실제 자소서 본문은 MySQL에만 저장한다. 이 분리가 주는 이점은 다음과 같다.

**인덱스 크기 최소화**: FAISS 인덱스는 메모리에 올려 쓰므로 크기가 작을수록 서버 기동이 빠르고 메모리 사용량이 낮다. 본문(수천 자)을 제외하고 임베딩과 ID만 저장하면 같은 장비에 더 많은 샘플을 담을 수 있다.

**본문 업데이트 비용 감소**: 자소서 오탈자 수정 같은 본문 변경은 MySQL `UPDATE` 한 번으로 끝나며, FAISS 인덱스를 재구축할 필요가 없다. 반면 임베딩이 바뀌는 본질적 변경(예: 텍스트 재작성)에만 인덱스를 재빌드한다.

**메타데이터 활용 유연성**: 등급(`grade`), 점수(`selfintro_score`) 같은 필터링 조건을 SQL `WHERE`로 표현할 수 있다. 벡터 DB에서 복합 메타데이터 필터는 구현이 까다롭거나 성능이 떨어지는 경우가 많다.

---

## 3. 클래스 설계

### 3.1 LangChain `BaseRetriever` 상속

`HybridRetriever`는 LangChain의 `BaseRetriever`를 상속한다. 이를 통해 다음과 같은 표준 인터페이스를 얻는다:

- `retriever.invoke(query)` — LCEL 체인에서 사용 가능
- `retriever.get_relevant_documents(query)` — 전통적 호출 방식
- LangSmith 자동 추적 (`@traceable` 데코레이터 활성화 시)

### 3.2 필드 정의

```python
class HybridRetriever(BaseRetriever):
    embeddings: any
    top_n: int = 3
    initial_k: int = 50
    vectorstore: FAISS = None
    index_folder: str = "faiss_index"
    _conn = PrivateAttr()
```

| 필드 | 의미 | 기본값 |
|---|---|---|
| `embeddings` | 쿼리 벡터화에 사용할 임베딩 모델 | (필수 주입) |
| `top_n` | 최종 반환 문서 수 | 3 |
| `initial_k` | FAISS 1차 후보 수 | 50 |
| `vectorstore` | 로드된 FAISS 인덱스 객체 | None (지연 로드) |
| `index_folder` | FAISS 인덱스 폴더 경로 | `faiss_index` |
| `_conn` | MySQL 커넥션 | `__init__`에서 생성 |

### 3.3 `initial_k`와 `top_n`의 역할 분리

FAISS에서 바로 `k=3`만 뽑지 않고 `initial_k=50`을 먼저 뽑는 이유는 **후처리 필터링 여지**를 두기 위함이다. 예를 들어 향후 `grade == 'high'`만 우선 선택하는 Peer-First 필터링이 활성화되면, 50개 중 조건에 맞는 상위 3개를 선정할 수 있다. 이 설계는 현재는 단순 상위 3개로 동작하나 확장을 준비한 것이다.

---

## 4. 검색 로직 상세

### 4.1 초기화 (`__init__`)

객체 생성 시 MySQL 커넥션을 열고 FAISS 인덱스를 로드한다. FAISS는 `allow_dangerous_deserialization=True`로 pickle 기반 로드를 허용하는데, 이는 직접 빌드한 신뢰 가능한 인덱스를 사용한다는 전제 하에 설정한 것이다.

```python
def __init__(self, db_config, **kwargs):
    super().__init__(**kwargs)
    self._conn = pymysql.connect(
        **db_config,
        cursorclass=pymysql.cursors.DictCursor
    )
    self._get_vector_index()
```

### 4.2 인덱스 로드 (`_get_vector_index`)

```python
self.vectorstore = FAISS.load_local(
    folder_path=self.index_folder,
    embeddings=self.embeddings,
    allow_dangerous_deserialization=True
)
```

로드 시점은 기본적으로 객체 생성 시이며, `vectorstore is None`인 경우 `_get_relevant_documents` 호출 시 지연 로드된다.

### 4.3 유사도 검색 (`_get_relevant_documents`)

```python
def _get_relevant_documents(self, query: str) -> List[Document]:
    if self.vectorstore is None:
        self._get_vector_index()

    # 1단계: FAISS 유사도 검색 (상위 initial_k)
    docs_and_scores = self.vectorstore.similarity_search_with_score(
        query, k=self.initial_k
    )
    
    # 2단계: score map 구성 (ID → (자소서점수, 유사도점수))
    score_map = {
        int(doc.page_content): (
            doc.metadata.get('selfintro_score', 0),
            float(score)
        )
        for doc, score in docs_and_scores
    }
    
    # 3단계: 상위 N개 선정
    candidates = [doc for doc, _ in docs_and_scores]
    final_candidate_docs = candidates[:self.top_n]
    target_db_ids = [int(d.page_content) for d in final_candidate_docs]
    
    # 4단계: MySQL에서 본문 페치
    return self._fetch_final_documents(target_db_ids, score_map)
```

### 4.4 본문 조회 (`_fetch_final_documents`)

```python
def _fetch_final_documents(
    self, db_ids: List[int], score_map: Dict[int, float]
) -> List[Document]:
    if not db_ids:
        return []
    
    self._conn.ping(reconnect=True)
    cursor = self._conn.cursor()
    
    try:
        format_strings = ','.join(['%s'] * len(db_ids))
        sql = f"""
        SELECT id, selfintro
        FROM applicant_records
        WHERE id IN ({format_strings})
        """
        cursor.execute(sql, tuple(db_ids))
        rows = cursor.fetchall()
        
        id_map = {r['id']: r for r in rows}
        
        # 원래 유사도 순서(db_ids) 유지
        final_docs = []
        for db_id in db_ids:
            if db_id in id_map:
                record = id_map[db_id]
                doc = Document(
                    page_content=record['selfintro'],
                    metadata={
                        "id": db_id,
                        "selfintro_score": score_map.get(db_id)[0],
                        "relevance_score": score_map.get(db_id)[1]
                    }
                )
                final_docs.append(doc)
        return final_docs
    except Error as e:
        print(f"❌ MySQL 에러: {e}")
        return []
    finally:
        cursor.close()
        self._conn.close()
```

### 4.5 FAISS Document의 `page_content`에 ID를 저장하는 이유

FAISS에 저장되는 Document의 `page_content`는 보통 실제 텍스트지만, 본 구조에서는 **레코드 ID(정수)를 문자열로 저장**한다. 이 설계의 의도는 명확하다. FAISS에는 검색에 필요한 최소 정보(벡터와 식별자)만 두고, 본문 조회는 MySQL이 책임지도록 역할을 완전히 분리하기 위함이다. `int(doc.page_content)`로 ID를 복원하여 MySQL 조회 키로 사용한다.

---

## 5. 인스턴스화 예시

`backend/services/chat_logic.py`에서 retriever는 다음과 같이 생성된다:

```python
from langchain_huggingface import HuggingFaceEmbeddings
from retriever import HybridRetriever

DB_CONFIG = {
    'host': os.getenv('HOST'),
    'port': int(os.getenv('PORT')),
    'user': os.getenv('USER'),
    'password': os.getenv('PASSWORD'),
    'db': os.getenv('DB'),
    'charset': 'utf8mb4'
    # TiDB 사용 시:
    # 'ssl_ca': ROOT_DIR / 'isrgrootx1.crt',
    # 'ssl_verify_cert': True,
}

hf_embeddings = HuggingFaceEmbeddings(
    model_name="Qwen/Qwen3-Embedding-0.6B",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

selfintro_retriever = HybridRetriever(
    db_config=DB_CONFIG,
    embeddings=hf_embeddings,
    top_n=3,
    initial_k=5,    # 실제 런타임 값 (chat_logic.py)
    index_folder=str(ROOT_DIR / "faiss_index_high")
)
```

운영 시에는 `initial_k=50`을 권장하나, 현재 샘플 데이터가 3건뿐이라 런타임 설정은 5로 낮춰 둔 상태다. 샘플 적재 이후 50으로 상향해야 Peer-First 필터링 효과를 얻을 수 있다.

---

## 6. 임베딩 정규화

`encode_kwargs={'normalize_embeddings': True}` 설정은 출력 벡터의 L2 norm을 1로 정규화한다. 이로 인해 FAISS가 기본적으로 사용하는 L2 distance가 실질적으로 cosine similarity와 동일한 순위를 매기게 된다. 한국어 텍스트 유사도 비교에서는 cosine이 L2보다 안정적인 결과를 보이므로, 정규화를 기본값으로 설정했다.

---

## 7. FAISS 인덱스 구축

### 7.1 폴더 구조

인덱스는 `faiss_index_high/` 폴더에 두 파일로 저장된다:

```
faiss_index_high/
├── index.faiss          # 벡터 인덱스 바이너리
└── index.pkl            # Document 메타데이터 (pickle)
```

### 7.2 빌드 스크립트 예시

v0.2.0 시점에는 빌드 스크립트가 레포에 포함되어 있지 않으며, 다음 버전에서 `scripts/embed/build_faiss_index.py`로 추가할 예정이다. 빌드 로직의 골격은 다음과 같다:

```python
# scripts/embed/build_faiss_index.py (예시)
import pymysql
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

conn = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()
cursor.execute("""
    SELECT id, selfintro, selfintro_score, grade
    FROM applicant_records
    WHERE grade = 'high'
""")
rows = cursor.fetchall()

docs = [
    Document(
        page_content=str(row['id']),    # ID를 page_content에 저장
        metadata={
            'selfintro': row['selfintro'],   # 임베딩 소스
            'selfintro_score': row['selfintro_score'],
            'grade': row['grade'],
        }
    )
    for row in rows
]

# selfintro 본문으로 임베딩 계산
texts_to_embed = [d.metadata['selfintro'] for d in docs]
embeddings = HuggingFaceEmbeddings(
    model_name="Qwen/Qwen3-Embedding-0.6B",
    encode_kwargs={'normalize_embeddings': True}
)

vectorstore = FAISS.from_texts(
    texts=texts_to_embed,
    embedding=embeddings,
    metadatas=[d.metadata for d in docs],
    ids=[d.page_content for d in docs],
)
vectorstore.save_local("faiss_index_high")
```

### 7.3 재빌드 주기

신규 자소서 추가 시 인덱스를 재빌드한다. 증분 빌드(`FAISS.add_texts`)도 가능하나, v0.2.0에서는 전체 빌드 방식을 택한다. 샘플 규모가 수천 건 수준에서는 전체 빌드 비용이 크지 않다.

---

## 8. 운영 고려사항

### 8.1 커넥션 관리

`__init__`에서 연 커넥션을 객체 수명 동안 유지한다. `_fetch_final_documents` 내에서 `self._conn.ping(reconnect=True)`로 유휴 상태의 단절을 복구한다. `finally` 블록에서 커넥션을 닫는 현재 코드는 개선이 필요하다: 인스턴스가 싱글톤으로 사용되므로 `finally`에서 닫으면 다음 요청 시 커넥션이 없다. v0.3.0에서 커넥션 풀(`DBUtils.PooledDB` 또는 SQLAlchemy)로 전환 예정이다.

### 8.2 메모리 사용량

FAISS 인덱스는 전체가 메모리에 로드된다. 1024차원 float32 벡터 1건당 약 4KB이므로, 1만 건이면 40MB 수준이다. 10만 건까지는 단일 컨테이너(2GB 메모리)로 충분하다.

### 8.3 동시성

FAISS 인덱스는 읽기 전용으로 사용되므로 스레드 안전하다. 반면 MySQL 커넥션은 동시 요청에 대비해 커넥션 풀로 전환해야 한다. 현재 구조는 uvicorn `--workers 1`에서만 안전하다.

---

## 9. 관측성

### 9.1 LangSmith 추적

`retriever.py` 내의 `@traceable(name="Vector Search")` 데코레이터는 현재 주석 처리되어 있다. v0.3.0에서 활성화하면 LangSmith 대시보드에서 쿼리, 검색된 문서 수, 소요 시간 등을 확인할 수 있다.

### 9.2 수동 로깅

MySQL 에러는 현재 `print()`로 출력된다. 구조화 로깅(JSON logger)으로 전환하여 Docker Compose의 `docker compose logs`에서 필터링 가능하게 할 예정이다.

---

## 10. 제약사항 및 향후 계획

### 10.1 현재 제약

**Peer-First 필터링 미활성**: `grade` 기반 필터링 코드(주석 처리됨)가 아직 활성화되지 않았다. 현재는 유사도 순서로만 상위 3개를 선정한다.

**샘플 수 부족**: 운영용 데이터가 `essay_samples.json` 3건과 미적재 MySQL 테이블뿐이라, 실제 검색 품질 검증이 불가능한 상태다.

**인덱스 빌드 스크립트 부재**: `faiss_index_high/` 폴더를 재현할 공식 스크립트가 레포에 없다.

### 10.2 v0.3.0 개선

| 항목 | 내용 |
|---|---|
| Peer-First 필터 | grade high → mid 순서 활성화 |
| 커넥션 풀 | pymysql 직접 사용 → SQLAlchemy 또는 PooledDB |
| 빌드 스크립트 | `scripts/embed/build_faiss_index.py` 추가 |
| LangSmith 추적 | `@traceable` 활성화 |
| 메트릭 수집 | Recall@3, MRR 기반 정기 평가 |

### 10.3 MySQL VECTOR 전환 검토

FAISS를 완전히 제거하고 `resume_vectors` 테이블의 `VECTOR(1024)` 컬럼과 `VECTOR_DISTANCE()` 함수로 대체하는 방안을 v0.4.0 최적화 단계에서 평가한다. 단일 DB로 운영 단순화 vs. 속도 저하의 트레이드오프를 벤치마크 후 결정한다.

---

## 11. 관련 문서

| 주제 | 문서 |
|---|---|
| RAG 파이프라인 전체 | `docs/wiki/model/rag_pipeline.md` |
| 임베딩 모델 | `docs/wiki/model/embedding.md` |
| DB 스키마 | `docs/wiki/backend/database.md` |
| 백엔드 구조 | `docs/wiki/backend/architecture.md` |

---

*last updated: 2026-04-22 | 조라에몽 팀*
