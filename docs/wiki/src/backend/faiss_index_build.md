# 🏗️ FAISS 인덱스 구축 가이드

> **문서 목적**: 데이터베이스(MySQL 9 / TiDB)에 적재된 합격 자소서 벡터 데이터를 고속 검색 가능한 로컬 FAISS 인덱스 파일로 변환하는 방법을 기술한다.  
> **최종 수정일**: 2026-04-26  
> **작성자**: 조라에몽 팀

---

## 1. 개요

Job-Pocket의 RAG 시스템은 검색 성능 극대화를 위해 **2단계 검색 구조**를 사용합니다. 
1. **벡터 검색**: 로컬 메모리에 로드된 FAISS 인덱스를 통해 유사 사례 ID 추출.
2. **원문 조회**: 추출된 ID로 MySQL에서 실제 자소서 본문 페치.

이 문서는 1단계 검색에 필요한 **FAISS 인덱스 파일(`index.faiss`, `index.pkl`)을 DB 데이터로부터 생성**하는 과정을 설명합니다.

---

## 2. 빌드 프로세스 상세

인덱스 빌드 프로세스는 다음 과정을 통해 수행됩니다.

### 2.1 데이터 로딩 (Extract)
시스템은 DB의 `applicant_records`와 `resume_vectors` 테이블을 조인하여 학습된 벡터 데이터를 로드합니다. 특히 TiDB/MySQL 9의 벡터 타입을 처리하기 위해 내부적으로 문자열 변환 함수(`VECTOR_TO_STRING`)를 활용합니다.

### 2.2 인덱스 생성 (Build)
- **Inner Product 전략**: FAISS의 `MAX_INNER_PRODUCT` 전략을 사용합니다. 
- **코사인 유사도 보장**: 임베딩 생성 시 이미 정규화(`normalize_embeddings=True`)를 거쳤으므로, 내적 연산 결과는 수학적으로 **코사인 유사도**와 일치하게 됩니다.

### 2.3 로컬 저장 (Save)
생성된 인덱스는 백엔드 서버가 기동 시 참조하는 표준 경로인 `backend/data/faiss_index_high`에 파일 형태로 저장됩니다.

---

## 3. 빌드 실행

데이터 인제스션 파이프라인(`database/ingestion`)을 통해 DB에 데이터 적재가 완료된 후, 제공되는 빌드 도구를 실행하여 인덱스를 생성합니다.

- **기본 저장 경로**: `backend/data/faiss_index_high/`
- **생성되는 파일**:
  - `index.faiss`: 벡터 데이터 인덱스 바이너리.
  - `index.pkl`: 문서 ID 및 메타데이터를 담은 파이클 파일.

---

## 💻 빌드 소스코드 (Reference)

아래는 DB에서 벡터를 추출하여 FAISS 인덱스를 생성하는 핵심 로직입니다.

<details>
<summary>📂 FAISS 인덱스 빌더 코드 보기</summary>

```python
import json
import numpy as np
import sys
from pathlib import Path
from sqlalchemy import text
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_huggingface import HuggingFaceEmbeddings

# FAISS 인덱스를 생성하고 로컬 파일로 저장하는 핵심 클래스
class FAISSIndexBuilder:
    def __init__(self, save_path: str, embedding_config: dict):
        self.save_path = save_path
        self.embeddings = HuggingFaceEmbeddings(**embedding_config)

    def build_and_save(self, vector_engine):
        with vector_engine.connect() as conn:
            # 1. DB에서 벡터 데이터 로딩 (TiDB/MySQL 9)
            sql = text("""
                SELECT r.id, r.selfintro_score, VECTOR_TO_STRING(v.embedding) as embedding_str
                FROM applicant_records r
                JOIN resume_vectors v ON r.id = v.record_id
            """)
            result = conn.execute(sql)
            rows = result.mappings().all()

            # 2. 데이터 가공 및 벡터 변환
            metadatas, vectors, ids = [], [], []
            for r in rows:
                metadatas.append({"selfintro_score": r.get('selfintro_score', 0), "id": r['id']})
                ids.append(str(r['id']))
                vec = json.loads(r['embedding_str']) if r['embedding_str'] else [0.0]*1024
                vectors.append(vec)

            # 3. FAISS 빌드 (Inner Product 전략)
            text_embeddings = list(zip(ids, np.array(vectors).astype('float32')))
            vectorstore = FAISS.from_embeddings(
                text_embeddings=text_embeddings,
                embedding=self.embeddings,
                metadatas=metadatas,
                distance_strategy=DistanceStrategy.MAX_INNER_PRODUCT
            )

            # 4. 로컬 저장
            Path(self.save_path).mkdir(parents=True, exist_ok=True)
            vectorstore.save_local(self.save_path)
```
</details>

---

## 4. 운영 시 주의사항

1. **데이터 동기화**: DB의 `applicant_records` 데이터가 대량으로 추가되거나 수정된 경우, 반드시 이 스크립트를 재실행하여 FAISS 인덱스를 최신화해야 합니다.
2. **경로 설정**: 백엔드 서비스(`RetrievalService`)에서 참조하는 `index_folder` 경로와 빌더의 `save_path`가 일치해야 합니다.
3. **환경 변수**: DB 연결을 위해 `.env` 파일에 정의된 `VECTOR_DB_URL` 및 계정 정보가 올바르게 설정되어 있어야 합니다.

---
*Copyright (c) 2026 Team Joraemon*
