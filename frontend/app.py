import streamlit as st
import os
import base64

from utils.ui_components import apply_custom_css
from utils import api_client
from views import auth_view, resume_view, chat_view

# ==========================================
# 1. 페이지 기본 설정 및 세션 초기화
# ==========================================
st.set_page_config(
    page_title="JobPocket", page_icon="public/logo_light.png", layout="wide"
)
apply_custom_css()

DEFAULT_SESSION_VALUES = {
    "logged_in": False,
    "user_info": None,
    "messages": [],           # 현재 메인 화면의 채팅 내역
    "chat_history_list": [],  # 사이드바에 표시할 과거 전체 내역
    "page": "login",
    "menu": "chat",
    "reset_email": None,
    "selected_model": "GPT-4o-mini",
    "reset_code": None,
    "code_verified": False,
    "history_loaded_for": None,
    "show_welcome": True,
    "pending_prompt": None,
    "current_result_version": 0,
}
for key, value in DEFAULT_SESSION_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==========================================
# 2. 메인 라우팅 (로그인 전)
# ==========================================
if not st.session_state.logged_in:
    if st.session_state.page == "login":
        auth_view.login_view()
    elif st.session_state.page == "signup":
        auth_view.signup_view()
    elif st.session_state.page == "find_password":
        auth_view.find_password_view()
    elif st.session_state.page == "reset_password":
        auth_view.reset_password_view()

# ==========================================
# 3. 사이드바 및 메인 라우팅 (로그인 후)
# ==========================================
else:
    user_email = st.session_state.user_info["email"]
    user_name = st.session_state.user_info["username"]

    # [핵심] 로그인 직후: DB 내역은 사이드바 리스트에만 담고, 채팅창은 새 채팅(웰컴)으로 시작
    if st.session_state.history_loaded_for != user_email:
        st.session_state.chat_history_list = api_client.load_chat_history_api(user_email)
        st.session_state.messages = [] 
        st.session_state.history_loaded_for = user_email
        st.session_state.show_welcome = True

    with st.sidebar:
        img_path = "public/logo_light.png"
        if os.path.exists(img_path):
            with open(img_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<div style="text-align:center;"><img src="data:image/png;base64,{encoded}" width="130" style="border-radius:15px; margin-bottom:20px;"></div>',
                unsafe_allow_html=True,
            )

        # 👤 유저 정보 팝오버
        with st.popover(f"👤 {user_name}님", use_container_width=True):
            if st.button("📁 내 스펙 보관함", use_container_width=True):
                st.session_state.menu = "resume"
                st.rerun()

        # [새 채팅 버튼]: 화면(messages)만 비우고 웰컴 페이지로 이동 (DB 기록 유지)
        if st.button("💬 새 채팅 (AI 자소서 첨삭)", use_container_width=True):
            st.session_state.menu = "chat"
            st.session_state.messages = []
            st.session_state.show_welcome = True
            st.session_state.current_result_version = 0
            st.rerun()

        st.write("")
        # 1. 텍스트 영역 폰트 크기 대폭 축소 (HTML 직접 주입)
        st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #4B5563; margin-bottom: 4px;'>🧠 AI 모델 설정</div>", unsafe_allow_html=True)
        
        # 2. 셀렉트박스 내부 글자 크기 축소 CSS
        st.markdown("""
            <style>
            [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] {
                font-size: 0.8rem !important;
            }
            ul[data-baseweb="menu"] li {
                font-size: 0.8rem !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # 3. [핵심] 토글 내부에 설명 추가 (format_func 활용)
        model_descriptions = {
            "GPT-4o-mini": "⚡ GPT-4o-mini (기본 첨삭)",
            "GPT-OSS-120B (Groq)": "🧠 GPT-OSS-120B (심층 첨삭)"
        }

        st.session_state.selected_model = st.selectbox(
            "엔진 선택",    
            ["GPT-4o-mini", "GPT-OSS-120B (Groq)"],
            format_func=lambda x: model_descriptions[x],
            index=0 if st.session_state.selected_model == "GPT-4o-mini" else 1,
            label_visibility="collapsed",
        )

        # 대화 기록 영역
        st.write("")
        col_hist_title, col_hist_btn = st.columns([7, 3])
        with col_hist_title:
            st.markdown("#### 📝 대화 기록")
        with col_hist_btn:
            if st.button("🗑️", key="clear_all_btn", use_container_width=True):
                api_client.delete_chat_history_api(user_email) # DB 삭제
                st.session_state.chat_history_list = []        # 사이드바 비우기
                st.session_state.messages = []                 # 메인 화면 비우기
                st.session_state.show_welcome = True
                st.session_state.current_result_version = 0
                st.rerun()

        # 사이드바 대화 기록 목록 표시 (chat_history_list 사용)
        if st.session_state.chat_history_list:
            user_questions = [m for m in st.session_state.chat_history_list if m["role"] == "user"]
            with st.container(height=300):
                for q in reversed(user_questions):
                    short_q = (q["content"][:15] + "...") if len(q["content"]) > 15 else q["content"]
                    st.markdown(f"<div style='padding:5px 0; font-size:0.9em; color:#555;'>💬 {short_q}</div>", unsafe_allow_html=True)
        else:
            st.caption("대화 기록이 없습니다.")

        st.markdown('<div class="sidebar-bottom-spacer"></div>', unsafe_allow_html=True)
        if st.button("로그아웃", use_container_width=True, key="logout_sidebar"):
            st.session_state.clear()
            st.rerun()

    # 메인 뷰 라우팅
    if st.session_state.menu == "chat":
        chat_view.chat_view()
    else:
        resume_view.mypage_view()