import re
import time
import streamlit as st
from utils import api_client

AI_AVATAR = "public/logo_light.png"
USER_AVATAR = "👤"

# ==========================================
# 1. 문자열 처리 및 데이터 추출 헬퍼 함수
# ==========================================

def get_result_label(content: str) -> str:
    if not content or not isinstance(content, str): return ""
    match = re.search(r"^\[(.+?)\]", content.strip())
    return match.group(1) if match else ""

def get_last_assistant_result() -> str:
    for msg in reversed(st.session_state.messages):
        if msg["role"] != "assistant": continue
        content = msg.get("content")
        if not content: continue
        label = get_result_label(content)
        if label == "자소서 초안" or label.endswith("수정안"):
            return content
    return ""

def extract_resume_text(content: str) -> str:
    if not content or not isinstance(content, str): return ""
    try:
        title_match = re.search(r"^\[(.+?)\]\s*", content.strip())
        if not title_match: return content.strip()

        remaining = content.strip()[title_match.end() :].lstrip()
        if remaining.startswith("반영 사항:"):
            lines = remaining.splitlines()
            remaining = "\n".join(lines[1:]).lstrip()

        split_token = "[평가 및 코멘트]"
        if split_token in remaining:
            return remaining.split(split_token)[0].strip()

        return remaining.strip()
    except Exception:
        return content.strip() if content else ""

def extract_evaluation_text(content: str) -> str:
    if not content or not isinstance(content, str): return ""
    split_token = "[평가 및 코멘트]"
    if split_token not in content: return ""
    return content.split(split_token, 1)[1].strip()

def parse_evaluation_for_display(evaluation_text: str) -> dict:
    result = {"rating": "", "reason": "", "points": []}
    if not evaluation_text: return result

    lines = [line.strip() for line in evaluation_text.splitlines() if line.strip()]
    point_mode = False

    for line in lines:
        if line.startswith("평가 결과:"): result["rating"] = line.replace("평가 결과:", "").strip()
        elif line.startswith("이유:"): result["reason"] = line.replace("이유:", "").strip()
        elif line.startswith("보완 포인트"): point_mode = True
        elif point_mode and (line.startswith("-") or line.startswith("•")):
            result["points"].append(line.lstrip("-•").strip())

    return result

# ==========================================
# 2. 수정 요청 및 프롬프트 생성 로직
# ==========================================

def point_to_revision_prompt(point: str) -> str:
    point = point.strip()
    if "첫 문장" in point: return "이 결과의 첫 문장이 더 선명하고 구체적으로 드러나도록 수정해줘."
    if "마지막 문단" in point: return "이 결과의 마지막 문단이 더 자연스럽고 현실적인 마무리가 되도록 수정해줘."
    if "지원동기" in point or "지원 이유" in point: return "이 결과에서 지원동기가 더 또렷하게 드러나도록 수정해줘."
    if "갈등" in point and ("방식" in point or "해결" in point): return "이 결과에서 갈등이 생긴 이유와 그것을 어떤 방식으로 조율하고 해결했는지가 더 분명히 드러나도록 수정해줘."
    if "경험" in point and "연결" in point: return "이 결과에서 내 경험과 지원 직무의 연결이 더 분명하게 드러나도록 수정해줘."
    if "직무" in point: return "이 결과가 지원 직무와 더 잘 맞아 보이도록 수정해줘."
    if "구체" in point: return "이 결과를 조금 더 구체적으로 보완해줘."
    if "담백" in point or "과장" in point: return "이 결과를 더 담백하고 과장 없는 문장으로 다듬어줘."
    if "분량" in point or "글자 수" in point or "700자" in point: return "이 결과를 글자 수 조건에 더 잘 맞도록 조정해줘."
    return f"다음 보완 포인트를 반영해서 수정해줘: {point}"

def build_change_summary_for_quick_action(prompt: str) -> str:
    if "첫 문장" in prompt: return "첫 문장이 더 선명하게 보이도록 수정했습니다."
    if "사례" in prompt or "연결" in prompt: return "경험과 직무의 연결이 더 드러나도록 수정했습니다."
    if "더 담백하게" in prompt: return "문장을 조금 더 담백한 톤으로 다듬었습니다."
    if "700자" in prompt: return "요청한 글자 수에 맞춰 분량을 조정했습니다."
    if "지원동기" in prompt: return "지원 이유가 더 또렷하게 드러나도록 수정했습니다."
    if "마지막 문단" in prompt: return "마지막 문단을 중심으로 수정했습니다."
    if "구체적" in prompt or "구체" in prompt: return "핵심 문장을 조금 더 구체적으로 보완했습니다."
    if "직무" in prompt: return "지원 직무와의 연결이 더 분명하게 드러나도록 수정했습니다."
    return "요청하신 방향을 반영해 수정했습니다."

# ==========================================
# 3. UI 렌더링 함수
# ==========================================

def render_evaluation_card(content: str, message_index: int):
    evaluation_text = extract_evaluation_text(content)
    parsed = parse_evaluation_for_display(evaluation_text)
    if not evaluation_text: return []

    rating, reason, points = parsed.get("rating", ""), parsed.get("reason", ""), parsed.get("points", [])
    st.markdown("### 평가 및 코멘트")
    if rating: st.markdown(f"**평가 결과:** {rating}")
    if reason: st.markdown(f"**이유:** {reason}")
    if points:
        st.markdown("**보완 포인트**")
        for idx, point in enumerate(points):
            col_text, col_btn = st.columns([5, 1.2])
            with col_text: st.markdown(f"- {point}")
            with col_btn:
                prompt_text = point_to_revision_prompt(point)
                if st.button("적용", key=f"eval_btn_{message_index}_{idx}", use_container_width=True):
                    st.session_state.pending_prompt = prompt_text
                    st.rerun()
    return points

def render_assistant_message(content: str, message_index: int):
    label = get_result_label(content)
    is_result_message = label == "자소서 초안" or label.endswith("수정안")

    if is_result_message:
        body_text = extract_resume_text(content)
        st.markdown(f"[{label}]")
        st.write("")
        st.markdown(body_text)
        caption = "📋 최신 수정본입니다. 아래 탭을 열어 본문만 쉽게 복사하세요." if label.endswith("수정안") else "📋 아래 탭을 열어 자소서 본문만 쉽게 복사하세요."
        st.caption(caption)
        with st.expander("📄 복사하기"): 
            st.code(body_text, language="plaintext")
        st.divider()
        
        render_evaluation_card(content, message_index)
        st.write("")
        
        feedback_title = "이 수정안이 마음에 드시나요?" if label.endswith("수정안") else "이 초안이 마음에 드시나요?"
        st.markdown(f"<div style='text-align:center;'>{feedback_title}</div>", unsafe_allow_html=True)
        
        feedback_key = f"feedback_{message_index}"
        if feedback_key not in st.session_state: st.session_state[feedback_key] = None
        
        center_cols = st.columns([4, 1, 1, 4])
        if st.session_state[feedback_key] is None:
            with center_cols[1]:
                if st.button("👍", key=f"good_{message_index}", use_container_width=True):
                    st.session_state[feedback_key] = "good"; st.rerun()
            with center_cols[2]:
                if st.button("👎", key=f"bad_{message_index}", use_container_width=True):
                    st.session_state[feedback_key] = "bad"; st.rerun()
        else:
            fb = "👍" if st.session_state[feedback_key] == "good" else "👎"
            st.markdown(f"<div style='text-align:center; color:#3B82F6;'>✓ 평가 완료: {fb}</div>", unsafe_allow_html=True)
            if fb == "👎": 
                st.info("어떤 부분이 아쉬웠는지 말씀해 주세요. 예: 첫 문장 구체화, 더 담백하게, 마지막 문단 수정")
    else:
        st.markdown(content)

def render_progress_card():
    st.markdown("""
        <div class="progress-card">
            <b>진행 단계</b>
            1. 문항과 요청 정보 정리<br>
            2. EXAONE 모델로 초안 생성 또는 기존 결과 분석<br>
            3. API 모델로 문장 정리 또는 수정 반영<br>
            4. 글자 수와 전체 흐름 최종 점검
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. AI 응답 생성 메인 로직
# ==========================================

def is_revision_request(prompt: str) -> bool:
    revision_keywords = ["수정", "고쳐", "다듬", "줄여", "늘려", "바꿔", "다시 써", "마지막 문단", "첫 문장", "담백", "구체적", "지원동기", "톤", "문장", "700자", "500자", "1000자", "사례", "연결", "직무"]
    return any(k in prompt for k in revision_keywords)

def generate_response_with_progress(prompt: str, user_info: tuple, selected_model: str):
    status_box, step_box = st.empty(), st.empty()
    render_progress_card()

    last_result_full = get_last_assistant_result()
    last_result_body = extract_resume_text(last_result_full) if last_result_full else ""

    status_box.info("입력 내용을 분석하고 있습니다.")
    step_box.caption("1/4 문항과 요청 정보를 정리하고 있습니다.")
    parsed_data = api_client.parse_request_api(prompt, selected_model)
    time.sleep(0.1)

    if last_result_body and is_revision_request(prompt):
        status_box.info("직전 결과를 바탕으로 수정 요청을 반영하고 있습니다.")
        step_box.caption("2/4 기존 결과를 기반으로 수정 중입니다.")
        revised = api_client.revise_existing_draft_api(last_result_body, prompt, selected_model)

        status_box.info("수정된 문장을 더 자연스럽게 정리하고 있습니다.")
        step_box.caption("3/4 문장 흐름과 표현을 정리하고 있습니다.")
        refined = api_client.refine_with_api_api(revised, parsed_data, selected_model)

        status_box.info("최종 길이와 전체 흐름을 점검하고 있습니다.")
        step_box.caption("4/4 글자 수와 전체 흐름을 최종 점검하고 있습니다.")
        adjusted = api_client.fit_length_api(refined, parsed_data, selected_model)

        st.session_state.current_result_version += 1
        result_label = f"{st.session_state.current_result_version}차 수정안"
        change_summary = build_change_summary_for_quick_action(prompt)

        final_response = api_client.build_final_response_api(
            adjusted, parsed_data, selected_model, result_label=result_label, change_summary=change_summary
        )
        status_box.success("수정안이 준비되었습니다."); step_box.empty()
        return final_response

    company_name = parsed_data.get("company") or "미기재"
    question_name = parsed_data.get("question") or "자기소개서 문항"
    status_box.info(f"회사/문항 정보를 정리했습니다. ({company_name} / {question_name})")
    
    step_box.caption("2/4 EXAONE 모델이 초안을 작성하고 있습니다.")
    local_draft = api_client.generate_exaone_draft_api(parsed_data, user_info, selected_model)

    status_box.info("EXAONE 초안이 생성되었습니다. 문장 흐름을 다듬고 있습니다.")
    step_box.caption("3/4 API 모델이 문장을 다듬고 있습니다.")
    refined = api_client.refine_with_api_api(local_draft, parsed_data, selected_model)

    status_box.info("최종 문장 길이와 전체 흐름을 점검하고 있습니다.")
    step_box.caption("4/4 글자 수와 전체 흐름을 최종 점검하고 있습니다.")
    adjusted = api_client.fit_length_api(refined, parsed_data, selected_model)

    st.session_state.current_result_version = 0
    final_response = api_client.build_final_response_api(
        adjusted, parsed_data, selected_model, result_label="자소서 초안", change_summary=None
    )
    status_box.success("초안 생성이 완료되었습니다."); step_box.empty()
    return final_response

def process_prompt(prompt: str, user_email: str):
    """사용자 입력을 처리하고, 메인 채팅창과 사이드바 기록을 동시 업데이트합니다."""
    # 유저 메시지 저장 및 추가
    user_msg = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_msg)
    st.session_state.chat_history_list.append(user_msg) # 사이드바 업데이트
    api_client.save_chat_message_api(user_email, "user", prompt)
    
    with st.chat_message("user", avatar=USER_AVATAR): 
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AI_AVATAR):
        result_box = st.empty()
        try:
            response = generate_response_with_progress(
                prompt=prompt, 
                user_info=st.session_state.user_info, 
                selected_model=st.session_state.selected_model
            )
            result_box.markdown(response)
            
            # AI 메시지 저장 및 추가
            ai_msg = {"role": "assistant", "content": response}
            st.session_state.messages.append(ai_msg)
            st.session_state.chat_history_list.append(ai_msg) # 사이드바 업데이트
            api_client.save_chat_message_api(user_email, "assistant", response)
            
        except Exception as e:
            error_message = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
            result_box.error(error_message)
            st.info("잠시 후 다시 시도해 주세요. 같은 요청을 조금 더 구체적으로 적어주시면 도움이 됩니다.")
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            api_client.save_chat_message_api(user_email, "assistant", error_message)
    st.rerun()

def get_chat_input_placeholder() -> str:
    last_result = get_last_assistant_result()
    if not last_result: return "지원 회사/직무/문항을 입력해 주세요!"
    label = get_result_label(last_result)
    if label == "자소서 초안": return "생성된 초안의 수정 방향을 말씀해 주세요!"
    if label.endswith("수정안"): return "추가 수정 방향이나 문장 변경 요청을 말씀해 주세요!"
    return "지원 회사/직무/문항을 입력하거나, 수정 방향을 말씀해 주세요!"

# ==========================================
# 5. 메인 뷰 함수
# ==========================================

def chat_view():
    user_email = st.session_state.user_info["email"]
    
    if "show_welcome" not in st.session_state: 
        st.session_state.show_welcome = not bool(st.session_state.messages)

    # [웰컴 페이지]
    if st.session_state.show_welcome:
        user_name = st.session_state.user_info["username"]
        st.markdown(f"""
            <div style="background-color: #F0F8FF; padding: 2.5rem; border-radius: 15px; text-align: center; border: 2px solid #3B82F6; margin-top: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h2 style="color: #3B82F6; margin-bottom: 1rem; font-weight: 800;">반갑습니다, {user_name}님! 👋</h2>
                <p style="font-size: 1.2rem; color: #333; margin-bottom: 1.5rem;"><strong>JobPocket</strong>이 여러분의 합격 여정을 함께합니다.</p>
                <div style="text-align: left; display: inline-block; margin-bottom: 2rem; color: #555; font-size: 1.05rem; line-height: 2;">
                    🚀 <b>내 스펙 기반:</b> 입력한 경험을 바탕으로 팩트 중심 초안 생성<br>
                    🤖 <b>듀얼 모델 지원:</b> 빠른 초안 생성의 GPT-4o-mini와 심층 분석의 GPT-OSS-120B 선택 가능<br>
                    📝 <b>대화형 수정:</b> 초안 생성 후 문장별 수정, 톤 변경, 길이 조정 가능
                </div>
            </div>
        """, unsafe_allow_html=True)
        _, col_btn, _ = st.columns([1, 1, 1])
        with col_btn:
            if st.button("🚀 대화 시작하기", use_container_width=True, type="primary"):
                st.session_state.show_welcome = False
                if not st.session_state.messages:
                    greeting = "안녕하세요! 지원하시려는 **회사와 직무**, 그리고 **자기소개서 문항**을 편하게 남겨주세요. 😊"
                    # 첫 인사말도 메인창과 사이드바 동시 업데이트
                    st.session_state.messages.append({"role": "assistant", "content": greeting})
                    st.session_state.chat_history_list.append({"role": "assistant", "content": greeting})
                    api_client.save_chat_message_api(user_email, "assistant", greeting)
                st.rerun()
        return

    # [채팅 인터페이스]
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar=USER_AVATAR if message["role"] == "user" else AI_AVATAR):
            if message["role"] == "assistant": 
                render_assistant_message(message["content"], i)
            else: 
                st.markdown(message["content"])

    if st.session_state.get("pending_prompt"):
        pending = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        process_prompt(pending, user_email)
        return

    if prompt := st.chat_input(get_chat_input_placeholder()): 
        process_prompt(prompt, user_email)