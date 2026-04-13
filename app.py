import streamlit as st
import google.generativeai as genai
import time
import os
# [추가됨] 구글 API 에러를 부드럽게 넘기기 위한 방어막 부품
from google.api_core.exceptions import ResourceExhausted

# ==========================================
# 🔐 보안 접속 세팅
# ==========================================
SET_PASSWORD = "0366" 
# ==========================================

# 1. 화면 기본 설정
st.set_page_config(page_title="검단탑병원 인증 AI", page_icon="🏅", layout="wide", initial_sidebar_state="expanded")

# 2. B2B 엔터프라이즈급 CSS 적용
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    .stApp { background-color: #f0f2f5; }
    
    /* 사이드바 메뉴 가리기 (버튼은 살림) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background-color: transparent !important;}
    
    .block-container { padding-top: 2rem; }
    
    /* 프리미엄 대시보드 헤더 */
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 20px 30px; border-radius: 12px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 10px 20px rgba(0, 51, 102, 0.15);
        margin-bottom: 25px; border-left: 5px solid #8CC63F;
    }
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; font-weight: 800; color: white; letter-spacing: -0.5px; }
    .enterprise-header .sys-info { text-align: right; font-size: 0.85rem; opacity: 0.9; }
    .badge { background: #8CC63F; color: #003366; padding: 4px 10px; border-radius: 4px; font-weight: bold; margin-bottom:5px; display:inline-block;}
    
    /* 탭(Tabs) 고급화 */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: white; padding: 10px 20px 0px 20px; border-radius: 10px 10px 0 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"] { height: 50px; font-size: 1.05rem; font-weight: 600; color: #555; }
    .stTabs [aria-selected="true"] { color: #005691 !important; border-bottom-color: #005691 !important; border-bottom-width: 3px !important; }
    
    /* 채팅창 입체감 */
    .stChatMessage { background-color: white; border: 1px solid #e1e4e8; border-radius: 10px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); margin-bottom: 15px;}
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #ffffff; } 
    [data-testid="stChatMessage"]:nth-child(even) { background-color: #f8fafc; border-left: 4px solid #005691; } 
</style>
""", unsafe_allow_html=True)

# 3. 로그인 화면 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"):
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; margin:20px 0; font-weight:700;'>인증조사 마스터 AI 통합 시스템</h3>", unsafe_allow_html=True)
        pwd = st.text_input("보안 접근 코드를 입력하십시오.", type="password")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        elif pwd:
            st.error("⚠️ 인가되지 않은 코드입니다.")
    st.stop()

# ==========================================
# 🚀 메인 시스템 (대시보드 UI)
# ==========================================

# 4. 사이드바 
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"):
        st.image("검단탑병원-로고_고화질.png", use_container_width=True)
    
    st.markdown("---")
    st.markdown("<div style='background:#f4f6f9; padding:15px; border-radius:8px; border:1px solid #e1e4e8;'>", unsafe_allow_html=True)
    st.markdown("🔒 **접속 등급:** 관리자 (1급)<br>📡 **서버 상태:** 최적화<br>📚 **지식 DB:** 2024 통합 지침서", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("🔄 시스템 메모리 정리", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    if st.button("🔒 안전 로그아웃", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# 5. 엔터프라이즈 헤더
st.markdown("""
<div class='enterprise-header'>
    <div>
        <div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div>
        <h1>🏅 인증조사 마스터 AI</h1>
    </div>
    <div class='sys-info'>
        🟢 SYSTEM ONLINE<br>
        ⚡ LATENCY: 8ms<br>
        🛡️ ENCRYPTED SESSION
    </div>
</div>
""", unsafe_allow_html=True)

# 6. AI 엔진 세팅 (한국어 강제 족쇄)
genai.configure(api_key="AIzaSyAN0iPMwBCkzoJZm8Hn2FDyiHKePjVxx8s")
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction="너는 검단탑병원의 '인증조사 마스터 AI'야. [절대 규칙]: 모든 답변과 질문은 반드시 100% 한국어로만 자연스럽게 작성해. 'Rationale', 'Incorrect' 같은 영어 단어나 문장은 절대 쓰지 마."
)

@st.cache_resource
def get_pdf():
    files = []
    existing = {f.display_name: f for f in genai.list_files()}
    for d, p in {"Guide_DB": "guide.pdf", "Manual_DB": "manual2.pdf"}.items():
        if d in existing: files.append(existing[d])
        else:
            f = genai.upload_file(path=p, display_name=d)
            while f.state.name == 'PROCESSING': time.sleep(0.5)
            files.append(genai.get_file(f.name))
    return files

pdf_files = get_pdf()

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# ==========================================
# ⚡ [핵심] 에러 방어막이 탑재된 초고속 스트리밍 함수
# ==========================================
def fast_stream(prompt_text, mode):
    if mode == "search": yield "✅ **[시스템] 지침서 DB를 스캔 중입니다...**\n\n"
    elif mode == "eval": yield "🕵️‍♂️ **[답변 분석] 제출하신 내용을 규정과 대조합니다...**\n\n"
    elif mode == "question": yield "🕵️‍♂️ **[신규 질문] 실전 모의고사를 생성 중입니다...**\n\n"

    try:
        response = model.generate_content([pdf_files[0], pdf_files[1], prompt_text], stream=True)
        for chunk in response:
            if chunk.text: yield chunk.text
    except ResourceExhausted:
        # 1분 제한에 걸렸을 때 빨간 에러창 대신 출력되는 문구
        yield "\n\n⚠️ **[시스템 과부하 알림]**\n현재 접속량이 많아 AI 코어 보호를 위해 일시적으로 연결이 제한되었습니다. **약 1분(60초) 뒤에 다시 시도**해 주십시오."
    except Exception as e:
        yield f"\n\n⚠️ **[시스템 오류]** 서버 처리 중 문제가 발생했습니다. ({e})"

# ==========================================
# 🗂️ 탭 구조
# ==========================================
tab1, tab2 = st.tabs(["🔍 통합 규정 검색 DB", "🕵️‍♂️ AI 감독관 실전 훈련"])

# ------------------------------------------
# 탭 1: 일반 검색
# ------------------------------------------
with tab1:
    st.info("💡 질문하시면 지침서를 기반으로 가장 빠르고 정확하게 답변합니다.")
    for m in st.session_state.search_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("검색할 규정이나 지침을 입력하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            full_response = st.write_stream(fast_stream(f"질문:{prompt} (반드시 한국어로만 답해)", "search"))
        st.session_state.search_msgs.append({"role": "assistant", "content": full_response})

# ------------------------------------------
# 탭 2: 연속 감독관 모드
# ------------------------------------------
with tab2:
    st.info("💡 답변을 제출하면 즉시 채점 후, 새로운 질문을 자동으로 생성합니다.")
    for m in st.session_state.train_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if st.session_state.current_q is None:
        with st.chat_message("assistant"):
            q_prompt = "인증평가 현장에서 직원에게 물어볼 법한 짧은 규정 질문 딱 1개만 해줘. 부연설명이나 영어는 절대 쓰지 말고 오직 질문 한 문장만 한국어로 해."
            q_text = st.write_stream(fast_stream(q_prompt, "question"))
            st.session_state.current_q = q_text
            st.session_state.train_msgs.append({"role": "assistant", "content": q_text})

    if train_prompt := st.chat_input("감독관의 질문에 답변하십시오...", key="train_input"):
        st.session_state.train_msgs.append({"role": "user", "content": train_prompt})
        with st.chat_message("user"): st.markdown(train_prompt)

        with st.chat_message("assistant"):
            eval_prompt = f"질문 '{st.session_state.current_q}'에 대한 사용자의 답변 '{train_prompt}'을 평가해줘. 반드시 100% 한국어로만 작성해. 정답/오답 여부와 이유를 지침서 근거로 짧게 설명해."
            eval_text = st.write_stream(fast_stream(eval_prompt, "eval"))
            st.session_state.train_msgs.append({"role": "assistant", "content": eval_text})
        
        with st.chat_message("assistant"):
            st.markdown("---")
            next_q_prompt = "이전과 다른 내용으로 새로운 인증평가 짧은 질문 1개만 해줘. 영어 절대 쓰지 말고 한국어 질문 한 문장만 출력해."
            next_q_text = st.write_stream(fast_stream(next_q_prompt, "question"))
            st.session_state.current_q = next_q_text
            st.session_state.train_msgs.append({"role": "assistant", "content": f"---\n{next_q_text}"})
