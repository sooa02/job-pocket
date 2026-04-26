# 🔍 검색(Retrieval) 품질 평가 방법론

> **문서 목적**: Job-Pocket RAG 시스템의 검색 단계 정확도를 측정하기 위한 지표 정의와 평가 실행 가이드를 기술한다.  
> **최종 수정일**: 2026-04-26  
> **작성자**: 조라에몽 팀

---

## 1. 평가 개요

RAG 기반 서비스에서 검색 품질은 생성 품질의 상한선을 결정합니다. Job-Pocket은 단순히 임베딩 유사도가 높은 문서를 찾는 것을 넘어, 사용자의 **기술적 맥락(Tech Stack)**과 일치하는 합격 사례가 추출되는지 정량적으로 평가합니다.

---

## 2. 핵심 지표: TMR (Tech Matching Rate)

**TMR(기술 스택 매칭률)**은 Job-Pocket이 독자적으로 정의하여 사용하는 핵심 검색 지표입니다.

### 2.1 정의 및 계산식
사용자의 이력 정보에서 추출된 주요 기술 키워드가 검색된 자소서 샘플 내에 얼마나 포함되어 있는지를 측정합니다.

$$TMR = \frac{|Keywords_{Query} \cap Keywords_{Sample}|}{|Keywords_{Query}|}$$

- **Keywords_{Query}**: 사용자의 프로필(`resume_cleaned`)에서 형태소 분석기(Kiwi)를 통해 추출된 기술 명사 리스트.
- **Keywords_{Sample}**: FAISS 검색을 통해 추출된 상위 3개 자소서 본문의 기술 키워드.

### 2.2 도입 배경
임베딩 유사도는 문장의 전체적인 톤과 구조에 영향을 많이 받습니다. 하지만 개발자 자소서에서는 "Java"를 요구하는데 "Python" 사례가 나오는 식의 미스매치를 방지해야 합니다. TMR은 이러한 **기술적 정합성**을 보장하는 안전장치 역할을 합니다.

---

## 3. 평가 프로세스

### 3.1 평가 데이터셋
`backend/tests/evaluation/datasets/` 내의 JSON/JSONL 데이터를 사용합니다.
- **Query**: 사용자의 가상 이력 데이터.
- **Position**: 타겟 직무 (AI, Backend, Frontend).

### 3.2 평가 루프
1. **Keyword Extraction**: 사용자의 쿼리에서 핵심 기술 스택을 추출합니다.
2. **FAISS Search**: 현재 시스템의 `RetrievalService`를 통해 유사 사례 ID를 추출합니다.
3. **Keyword Matching**: 검색된 본문 원문과 사용자의 기술 키워드를 대조합니다.
4. **Scoring**: 개별 쿼리별 TMR을 합산하여 전체 평균(Mean TMR)을 산출합니다.

---

## 4. 실행 방법

백엔드 평가 모듈을 통해 터미널에서 즉시 실행 가능합니다.

```bash
# 기본 평가 실행 (기본 데이터셋 사용)
python backend/tests/evaluation/run_retrieval_eval.py

# 특정 테스트 파일 지정 실행
python backend/tests/evaluation/run_retrieval_eval.py --file test_cases_v1.json
```

---

## 5. 결과 리포트 (REPORT.md)

평가 완료 후 `backend/tests/evaluation/results/` 폴더에 마크다운 형식의 리포트가 생성됩니다.
- **Summary**: 전체 평균 TMR, Recall@K, Latency 통계.
- **Details**: 개별 쿼리별 매칭 성공/실패 키워드 상세 리스트.

---
*last updated: 2026-04-26 | 조라에몽 팀*
