# 🔄 Job-Pocket 시퀀스 다이어그램

> **문서 목적**: Job-Pocket 서비스의 주요 사용자 시나리오를 시퀀스 다이어그램으로 기술하여 컴포넌트 간 상호작용과 API 호출 순서를 명확히 한다.
> **작성일**: 2026-04-22
> **버전**: v0.2.0

---

## 1. 시나리오 목록

| # | 시나리오 | 빈도 | 핵심 컴포넌트 |
|---|---|---|---|
| 1 | 회원가입 | 1회성 | Frontend, Backend, MySQL |
| 2 | 로그인 | 높음 | Frontend, Backend, MySQL |
| 3 | 이력 정보 저장 | 중간 | Frontend, Backend, MySQL |
| 4 | 자소서 생성 (6단계 파이프라인) | 높음 | 전체 컴포넌트 |
| 5 | 기존 자소서 수정 | 중간 | Frontend, Backend, LLM |
| 6 | 채팅 이력 조회 | 로그인 시 | Frontend, Backend, MySQL |
| 7 | 채팅 이력 삭제 | 낮음 | Frontend, Backend, MySQL |

---

## 2. 시나리오 1 — 회원가입

```mermaid
sequenceDiagram
    actor U as 사용자
    participant F as Frontend<br/>(auth_view)
    participant A as api_client
    participant B as Backend<br/>(/api/auth/signup)
    participant H as auth.py
    participant D as database.py
    participant M as MySQL
    
    U->>F: 회원가입 폼 제출<br/>(name, email, password)
    F->>A: signup_api(name, email, password)
    A->>B: POST /api/auth/signup<br/>{name, email, password}
    B->>H: hash_pw(password)
    H-->>B: SHA-256 hash
    B->>D: add_user_via_web(<br/>name, hash, email)
    D->>M: SELECT * FROM users WHERE email=?
    M-->>D: (없음)
    D->>M: INSERT INTO users (...)
    M-->>D: OK
    D-->>B: (True, "회원가입 성공")
    B-->>A: 200 {status: "success", detail: "회원가입 성공"}
    A-->>F: (True, "가입 성공")
    F-->>U: 로그인 페이지로 이동
    
    Note over B,D: 이메일 중복 시<br/>(False, "이미 가입된 이메일입니다.")<br/>→ 400 HTTPException
```

---

## 3. 시나리오 2 — 로그인

```mermaid
sequenceDiagram
    actor U as 사용자
    participant F as Frontend<br/>(auth_view)
    participant A as api_client
    participant B as Backend<br/>(/api/auth/login)
    participant H as auth.py
    participant D as database.py
    participant M as MySQL
    participant S as st.session_state
    
    U->>F: 로그인 폼 제출<br/>(email, password)
    F->>A: login_api(email, password)
    A->>B: POST /api/auth/login<br/>{email, password}
    B->>D: get_user(email)
    D->>M: SELECT FROM users WHERE email=?
    M-->>D: (username, hash, email, resume_data)
    D-->>B: user tuple
    B->>H: hash_pw(req.password)
    H-->>B: input_hash
    
    alt input_hash == stored_hash
        B-->>A: 200 {status: "success", user_info: [...]}
        A-->>F: (True, user_info)
        F->>S: logged_in = True<br/>user_info = [...]<br/>menu = "chat"
        F-->>U: 채팅 화면 리다이렉트
    else 불일치 or 유저 없음
        B-->>A: 401 {detail: "이메일 또는 비밀번호가 일치하지 않습니다."}
        A-->>F: (False, error_msg)
        F-->>U: 에러 표시
    end
```

### 3.1 세션 초기화 (로그인 직후)

로그인 성공 시 Frontend는 해당 사용자의 채팅 이력을 서버에서 로드한다:

```mermaid
sequenceDiagram
    participant F as Frontend<br/>(app.py)
    participant A as api_client
    participant B as Backend<br/>(/api/chat/history)
    participant M as MySQL
    
    Note over F: st.session_state.history_loaded_for<br/>≠ user_email
    
    F->>A: load_chat_history_api(email)
    A->>B: GET /api/chat/history/{email}
    B->>M: SELECT role, content FROM chat_history<br/>WHERE user_email=? ORDER BY created_at ASC
    M-->>B: rows
    B-->>A: {messages: [...]}
    A-->>F: messages list
    F->>F: st.session_state.messages = [...]<br/>history_loaded_for = email<br/>show_welcome = len(messages)==0
```

---

## 4. 시나리오 3 — 이력 정보 저장 (내 스펙 보관함)

```mermaid
sequenceDiagram
    actor U as 사용자
    participant F as Frontend<br/>(resume_view)
    participant A as api_client
    participant B as Backend<br/>(/api/resume)
    participant D as database.py
    participant M as MySQL
    
    U->>F: 저장 버튼 클릭
    F->>F: 폼 데이터 취합<br/>{personal, education, additional}
    F->>A: update_resume_data_api(email, data)
    A->>B: PUT /api/resume/{email}<br/>{personal: {}, education: {}, additional: {}}
    B->>D: update_resume_data(email, data_dict)
    D->>D: json.dumps(data_dict)
    D->>M: UPDATE users SET resume_data=?<br/>WHERE email=?
    M-->>D: rowcount
    D-->>B: success (bool)
    
    alt success
        B-->>A: 200 {status: "success"}
        A-->>F: True
        F-->>U: "저장되었습니다" 토스트
    else fail
        B-->>A: 400 {detail: "스펙 저장 실패"}
        A-->>F: False
        F-->>U: 에러 표시
    end
```

---

## 5. 시나리오 4 — 자소서 생성 (6단계 파이프라인)

가장 복잡한 핵심 시나리오로, 프론트엔드가 6개 API를 순차 호출한다.

### 5.1 전체 흐름

```mermaid
sequenceDiagram
    actor U as 사용자
    participant F as Frontend<br/>(chat_view)
    participant B as Backend
    participant R as HybridRetriever
    participant FAISS as FAISS Index
    participant M as MySQL
    participant L1 as EXAONE<br/>(로컬/RunPod)
    participant L2 as GPT-4o-mini<br/>or Groq
    
    U->>F: "네이버 백엔드 지원동기 500자"
    F->>F: 메시지 저장<br/>(role=user)
    
    rect rgb(240, 248, 255)
    Note over F,B: Step 1: Parse
    F->>B: POST /api/chat/step-parse<br/>{prompt, model}
    B->>L2: parse_user_request_regex<br/>→ (실패 시) LLM parse
    L2-->>B: {company, job, question_type, char_limit}
    B-->>F: parsed dict
    end
    
    rect rgb(255, 248, 240)
    Note over F,B: Step 2: Draft (RAG)
    F->>B: POST /api/chat/step-draft<br/>{prompt, user_info, model}
    B->>R: selfintro_retriever.invoke(query)
    R->>FAISS: similarity_search(k=50)
    FAISS-->>R: 50 candidates + scores
    R->>R: top-3 선정
    R->>M: SELECT selfintro WHERE id IN (...)
    M-->>R: 3 selfintro rows
    R-->>B: List[Document]
    B->>B: summarize_samples<br/>+ extract_style_rules
    B->>L1: build prompt + context
    L1-->>B: draft text
    B->>B: score_local_draft<br/>(품질 검증, 최대 3회 재시도)
    B-->>F: {draft}
    end
    
    rect rgb(240, 255, 240)
    Note over F,B: Step 3: Refine
    F->>B: POST /api/chat/step-refine<br/>{draft, prompt, model}
    B->>L2: refine prompt
    L2-->>B: refined text
    B-->>F: {refined}
    end
    
    rect rgb(255, 240, 255)
    Note over F,B: Step 4: Fit
    F->>B: POST /api/chat/step-fit<br/>{refined, prompt, model}
    B->>L2: length adjustment prompt
    L2-->>B: adjusted text
    B-->>F: {adjusted}
    end
    
    rect rgb(255, 255, 240)
    Note over F,B: Step 5-6: Evaluate + Final
    F->>B: POST /api/chat/step-final<br/>{adjusted, prompt, model, result_label}
    B->>L2: evaluate_draft_with_api
    L2-->>B: evaluation text
    B->>B: build_final_response<br/>(본문 + 평가 조립)
    B-->>F: {final_response}
    end
    
    F->>F: 메시지 저장 (role=assistant)
    F-->>U: 최종 자소서 + 평가 표시
```

### 5.2 Step 2의 품질 검증 재시도

```mermaid
sequenceDiagram
    participant B as chat_logic
    participant L as EXAONE
    
    loop attempt 0 to 2 (max 3회)
        B->>L: build_local_draft(prompt)
        L-->>B: draft text
        B->>B: score_local_draft(draft)
        
        alt 품질 통과
            B-->>B: return draft
        else 품질 미달
            Note over B: fail_reason을 프롬프트에<br/>추가 지시로 반영
            B->>B: working_message += reason
        end
    end
    
    Note over B: 3회 모두 실패 시<br/>마지막 draft 반환
```

### 5.3 품질 검증 항목

검증은 `score_local_draft` 함수가 수행하며, 다음 5가지를 순차 체크한다:

1. 최소 길이 220자
2. 문장 반복률 48% 미만
3. `char_limit` 대비 최소 55% 이상
4. 지원동기 문항인 경우 회사명 포함 및 첫 문단 40자 이상
5. 과장 표현 9종(`'차별화된 경쟁력 확보'`, `'혁신을 선도'` 등) 미포함

---

## 6. 시나리오 5 — 기존 자소서 수정

사용자가 생성된 초안에 대해 "첫 문장을 더 구체적으로"와 같이 수정 요청을 하는 경우다.

```mermaid
sequenceDiagram
    actor U as 사용자
    participant F as Frontend<br/>(chat_view)
    participant B as Backend
    participant L as LLM (GPT-4o-mini / Groq)
    
    U->>F: "첫 문장을 더 구체적으로"
    F->>F: get_last_assistant_result<br/>(기존 초안 추출)
    F->>F: extract_resume_text<br/>(본문만 분리)
    
    rect rgb(255, 240, 240)
    Note over F,B: Revise (Step 2 대체)
    F->>B: POST /api/chat/step-revise<br/>{existing_draft, revision_request, model}
    B->>L: revise_existing_draft prompt
    L-->>B: revised text
    B-->>F: {revised}
    end
    
    Note over F,B: 이후 Step 3~6은<br/>시나리오 4와 동일 (Refine → Fit → Final)
    
    F->>B: POST /api/chat/step-refine
    F->>B: POST /api/chat/step-fit
    F->>B: POST /api/chat/step-final<br/>(result_label="1차 수정안",<br/>change_summary="첫 문장 구체화")
    B-->>F: {final_response}
    F-->>U: 수정안 + 반영 사항 표시
```

### 6.1 수정본 라벨링

`result_label`은 수정 횟수에 따라 증가한다. Frontend는 `st.session_state.current_result_version`을 기준으로 `"1차 수정안"`, `"2차 수정안"`을 순차 생성한다. `change_summary` 필드는 수정 사항 요약을 담아 최종 응답의 "반영 사항:" 라인으로 표시된다.

---

## 7. 시나리오 6 — 채팅 이력 조회

로그인 직후 또는 페이지 새로고침 시 호출된다. 시나리오 2의 "로그인 직후 세션 초기화"와 동일하다. 주요 쿼리는 다음과 같다:

```sql
SELECT role, content 
FROM chat_history 
WHERE user_email = ? 
ORDER BY created_at ASC;
```

이력은 생성 시간순으로 정렬되어 가장 오래된 메시지부터 최신 메시지 순서로 반환된다. Frontend는 이를 `st.session_state.messages`에 그대로 할당하여 채팅 화면을 재구성한다.

---

## 8. 시나리오 7 — 채팅 이력 삭제

사용자가 사이드바의 🗑️ 버튼을 클릭하면 실행된다.

```mermaid
sequenceDiagram
    actor U as 사용자
    participant F as Frontend<br/>(app.py 사이드바)
    participant A as api_client
    participant B as Backend
    participant M as MySQL
    participant S as st.session_state
    
    U->>F: 🗑️ 클릭
    F->>A: delete_chat_history_api(email)
    A->>B: DELETE /api/chat/history/{email}
    B->>M: DELETE FROM chat_history<br/>WHERE user_email=?
    M-->>B: OK
    B-->>A: 200 {status: "success"}
    A-->>F: return
    
    F->>S: messages = []<br/>show_welcome = True<br/>current_result_version = 0
    F->>F: st.rerun()
    F-->>U: 초기 상태 화면
```

---

## 9. 메시지 저장 패턴

자소서 생성과 수정 과정에서 Frontend는 두 시점에 `/api/chat/message`를 호출하여 DB에 저장한다:

1. 사용자 입력 직후: `role="user"`, `content=사용자 원본 입력`
2. AI 응답 완료 직후: `role="assistant"`, `content=final_response 전체 문자열`

이 단순한 저장 구조는 대화를 재구성할 때 파싱이 용이하게 하는 대신, 저장 공간은 다소 낭비된다. v0.3.0에서 결과물을 본문(`body`)과 평가(`evaluation`)로 분리 저장하는 방안을 검토한다.

---

## 10. 에러 복구 전략

각 시퀀스의 에러 상황에서 Frontend가 처리하는 방식이다.

| 단계 | 실패 상황 | 복구 전략 |
|---|---|---|
| Parse 실패 | LLM 응답 JSON 파싱 불가 | Regex 결과로만 진행 (fallback) |
| Draft 품질 미달 | 3회 재시도 모두 실패 | 마지막 초안 그대로 반환 |
| Refine 실패 | LLM 호출 예외 | 원본 draft를 refined로 사용 (passthrough) |
| Fit 실패 | 글자 수 조정 실패 | refined를 adjusted로 사용 (passthrough) |
| Evaluate 실패 | LLM 호출 예외 | `fallback_evaluation_comment` 결정론적 평가 사용 |
| DB 저장 실패 | `/message` API 실패 | 사용자에게 표시하되 세션은 유지 |

대부분의 실패는 사용자 경험을 끊지 않도록 passthrough 또는 fallback으로 처리된다.

---

## 11. 관련 문서

| 주제 | 문서 |
|---|---|
| 시스템 개요 | `docs/wiki/architecture/overview.md` |
| RAG 파이프라인 | `docs/wiki/model/rag_pipeline.md` |
| API 명세 | `docs/wiki/backend/api_spec.md` |
| 백엔드 아키텍처 | `docs/wiki/backend/architecture.md` |
| 프론트엔드 구조 | `docs/wiki/frontend/architecture.md` |

---

*last updated: 2026-04-22 | 조라에몽 팀*
