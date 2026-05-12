import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
import random
import time
import base64

# ============================================================
# 🔑 [보안] Streamlit Secrets 및 API 키 연동
# ============================================================
try:
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다. 설정 확인이 필요합니다.")
    st.stop()

SET_PASSWORD = "0366"
SYSTEM_NAME = "검단탑병원 인증 AI 시스템"

st.set_page_config(
    page_title=SYSTEM_NAME,
    page_icon="🏅",
    layout="wide"
)

# ============================================================
# 🎨 [디자인] PC 고급 레이아웃 + 모바일 별도 압축 UX
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    :root {
        color-scheme: light !important;
    }

    html,
    body {
        color-scheme: light !important;
        background-color: #f8f9fa !important;
    }

    * {
        font-family: 'Pretendard', sans-serif;
        box-sizing: border-box;
    }

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        background-color: #f8f9fa !important;
        color: #111827 !important;
    }

    p, span, div, li, h1, h2, h3, h4, h5, label {
        color: #111827 !important;
    }

    [data-testid="stSidebar"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    [data-testid="stHeader"] {
        display: none !important;
        height: 0px !important;
    }

    #creatorBadge,
    .viewerBadge_container__1QSob,
    .stDeployButton,
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* ============================================================ */
    /* 🖥️ PC 레이아웃 */
    /* ============================================================ */

    .block-container {
        max-width: 1800px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
        padding-bottom: 7rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }

    .dashboard-header {
        background: linear-gradient(90deg, #003366 0%, #005691 100%) !important;
        padding: 25px 35px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 25px;
    }

    .dashboard-header img {
        height: 45px !important;
        flex-shrink: 0;
        background: #ffffff;
        padding: 5px;
        border-radius: 8px;
    }

    .dashboard-header * {
        color: #ffffff !important;
    }

    .dashboard-header h1 {
        margin: 0;
        font-size: 1.8rem !important;
        font-weight: 800;
        letter-spacing: -1px !important;
    }

    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        background-color: #ffffff !important;
        padding: 12px 20px !important;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        overflow: hidden !important;
    }

    div[role="radiogroup"] label {
        font-weight: 700 !important;
        color: #475569 !important;
        padding: 8px 16px !important;
        font-size: 1.05rem !important;
    }

    div[role="radiogroup"] label[data-baseweb="radio"]:has(input[checked]) * {
        color: #003366 !important;
    }

    .welcome-section {
        background-color: #ffffff !important;
        padding: 30px 32px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        min-height: 190px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 12px;
        margin-bottom: 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    .welcome-section h2 {
        color: #111827 !important;
        margin: 0;
        font-size: 1.55rem !important;
        font-weight: 800;
        letter-spacing: -0.6px;
        line-height: 1.35;
    }

    .welcome-section p {
        color: #475569 !important;
        margin: 0;
        font-size: 1.03rem !important;
        line-height: 1.65;
        word-break: keep-all;
    }

    .quick-card {
        background-color: #ffffff !important;
        padding: 24px 26px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        min-height: 190px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    .quick-prompts-title {
        margin: 0 0 14px 0;
        font-size: 1.12rem !important;
        color: #1e293b !important;
        font-weight: 800;
        letter-spacing: -0.3px;
    }

    div[data-testid="stButton"] button {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 25px !important;
        color: #005691 !important;
        font-weight: 600 !important;
        padding: 11px 18px !important;
        display: flex !important;
        justify-content: center !important;
        text-align: center !important;
        width: 100% !important;
        transition: all 0.2s ease-in-out;
        font-size: 0.93rem !important;
        line-height: 1.25 !important;
    }

    div[data-testid="stButton"] button:hover {
        border-color: #005691 !important;
        background-color: #f0f9ff !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }

    .answer-structure {
        background-color: #ffffff !important;
        padding: 25px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    .answer-structure h3 {
        color: #003366 !important;
        margin: 0 0 18px 0;
        font-size: 1.15rem !important;
        font-weight: 800;
        border-bottom: 2px solid #f1f5f9;
        padding-bottom: 12px;
    }

    .answer-structure ul {
        list-style: none;
        padding: 0;
        margin: 0;
    }

    .answer-structure li {
        margin-bottom: 18px;
        background: #f8f9fa;
        padding: 18px;
        border-radius: 10px;
        border-left: 5px solid #005691;
    }

    .answer-structure-title {
        font-weight: 700;
        color: #005691 !important;
        margin-bottom: 8px;
        font-size: 1.05rem !important;
    }

    .answer-structure-content {
        color: #475569 !important;
        font-size: 0.95rem !important;
        line-height: 1.6;
    }

    div[data-testid="stChatInput"] {
        max-width: 1800px !important;
        margin: 0 auto !important;
        left: 0 !important;
        right: 0 !important;
        padding-bottom: 25px !important;
        background-color: transparent !important;
    }

    div[data-testid="stChatInput"] > div {
        margin: 0 3rem !important;
        border: 2px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        color: #111827 !important;
    }

    div[data-testid="stChatInput"] > div:focus-within {
        border-color: #005691 !important;
    }

    div[data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
        opacity: 1 !important;
    }

    /* ============================================================ */
    /* 📱 모바일 전용 UX */
    /* ============================================================ */
    @media (max-width: 768px) {

        :root,
        html,
        body {
            color-scheme: light !important;
            background: #f8f9fa !important;
            background-color: #f8f9fa !important;
        }

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stBottom"],
        [data-testid="stBottomBlock"],
        [data-testid="stBottomBlockContainer"],
        div[data-testid="stChatInputContainer"] {
            background: #f8f9fa !important;
            background-color: #f8f9fa !important;
            color: #111827 !important;
        }

        * {
            -webkit-text-size-adjust: 100% !important;
            box-sizing: border-box !important;
        }

        p, span, div, li, h1, h2, h3, h4, h5, label {
            color: #111827 !important;
        }

        .block-container {
            max-width: 100% !important;
            padding-top: 0.55rem !important;
            padding-left: 0.7rem !important;
            padding-right: 0.7rem !important;
            padding-bottom: 6.2rem !important;
            overflow-x: hidden !important;
        }

        .dashboard-header {
            min-height: 54px !important;
            padding: 10px 12px !important;
            margin-bottom: 8px !important;
            border-radius: 10px !important;
            display: flex !important;
            flex-direction: row !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 10px !important;
            box-shadow: 0 3px 10px rgba(15, 23, 42, 0.12) !important;
        }

        .dashboard-header img {
            height: 30px !important;
            width: auto !important;
            padding: 3px !important;
            border-radius: 6px !important;
            flex-shrink: 0 !important;
        }

        .dashboard-header h1 {
            font-size: 1.05rem !important;
            line-height: 1.2 !important;
            margin: 0 !important;
            white-space: normal !important;
            word-break: keep-all !important;
            letter-spacing: -0.5px !important;
        }

        div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
            padding: 6px 7px !important;
            margin-bottom: 8px !important;
            border-radius: 10px !important;
            background-color: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
            overflow: hidden !important;
        }

        div[role="radiogroup"] {
            display: flex !important;
            flex-wrap: nowrap !important;
            gap: 2px !important;
            width: 100% !important;
            overflow: hidden !important;
        }

        div[role="radiogroup"] label {
            flex: 1 1 50% !important;
            min-width: 0 !important;
            padding: 5px 3px !important;
            font-size: 0.68rem !important;
            line-height: 1.1 !important;
            font-weight: 800 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            border-radius: 8px !important;
        }

        div[role="radiogroup"] label * {
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }

        .welcome-section {
            padding: 10px 12px !important;
            margin-bottom: 0 !important;
            border-radius: 10px !important;
            min-height: auto !important;
            background-color: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
            display: block !important;
        }

        .welcome-section h2 {
            font-size: 0.95rem !important;
            line-height: 1.22 !important;
            margin: 0 0 4px 0 !important;
            word-break: keep-all !important;
            letter-spacing: -0.4px !important;
        }

        .welcome-section p {
            font-size: 0.7rem !important;
            line-height: 1.32 !important;
            margin: 0 !important;
            word-break: keep-all !important;
            color: #475569 !important;
        }

        .welcome-section br {
            display: none !important;
        }

        .quick-card {
            padding: 10px 10px 9px 10px !important;
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            border-radius: 10px !important;
            min-height: auto !important;
            background-color: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
        }

        .quick-prompts-title {
            font-size: 0.82rem !important;
            line-height: 1.15 !important;
            margin: 0 0 6px 0 !important;
            font-weight: 800 !important;
            letter-spacing: -0.4px !important;
        }

        div[data-testid="stButton"] {
            margin-bottom: 2px !important;
        }

        div[data-testid="stButton"] button {
            min-height: 25px !important;
            height: 25px !important;
            padding: 3px 7px !important;
            border-radius: 14px !important;
            font-size: 0.63rem !important;
            line-height: 1.05 !important;
            font-weight: 800 !important;
            color: #005691 !important;
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: none !important;
            justify-content: center !important;
            text-align: center !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        div[data-testid="stButton"] button p {
            font-size: 0.63rem !important;
            line-height: 1.05 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        div[data-testid="stButton"] button:hover {
            transform: none !important;
            box-shadow: none !important;
        }

        .answer-structure {
            padding: 9px 10px !important;
            margin-top: 0 !important;
            margin-bottom: 4px !important;
            border-radius: 10px !important;
            background-color: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
        }

        .answer-structure h3 {
            font-size: 0.82rem !important;
            line-height: 1.15 !important;
            margin: 0 0 6px 0 !important;
            padding-bottom: 5px !important;
            border-bottom: 1px solid #edf2f7 !important;
            letter-spacing: -0.4px !important;
        }

        .answer-structure ul {
            display: grid !important;
            grid-template-columns: 1fr 1fr 1fr !important;
            gap: 4px !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        .answer-structure li {
            margin-bottom: 0 !important;
            padding: 6px 6px !important;
            border-radius: 8px !important;
            border-left: 3px solid #005691 !important;
            background-color: #f8fafc !important;
            min-height: 58px !important;
        }

        .answer-structure-title {
            font-size: 0.64rem !important;
            line-height: 1.1 !important;
            margin-bottom: 3px !important;
            font-weight: 800 !important;
            color: #005691 !important;
            letter-spacing: -0.3px !important;
        }

        .answer-structure-content {
            font-size: 0.55rem !important;
            line-height: 1.22 !important;
            color: #475569 !important;
            word-break: keep-all !important;
            letter-spacing: -0.25px !important;
        }

        .answer-structure-content br {
            display: none !important;
        }

        .element-container {
            margin-bottom: 0.28rem !important;
        }

        div[data-testid="stChatMessage"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 10px !important;
            padding: 8px !important;
            margin-bottom: 6px !important;
        }

        div[data-testid="stChatMessage"] p {
            font-size: 0.82rem !important;
            line-height: 1.45 !important;
            color: #111827 !important;
        }

        div[data-testid="stChatInput"] {
            max-width: 100% !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            padding: 7px 10px calc(9px + env(safe-area-inset-bottom)) 10px !important;
            background: #f8f9fa !important;
            background-color: #f8f9fa !important;
            border-top: 1px solid #e2e8f0 !important;
            box-shadow: 0 -3px 12px rgba(15, 23, 42, 0.06) !important;
        }

        div[data-testid="stChatInput"] > div {
            margin: 0 !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            border: 1.5px solid #cbd5e1 !important;
            border-radius: 16px !important;
            min-height: 42px !important;
            box-shadow: 0 2px 9px rgba(15, 23, 42, 0.08) !important;
            color: #111827 !important;
        }

        div[data-testid="stChatInput"] div,
        div[data-testid="stChatInput"] section,
        div[data-testid="stChatInput"] form,
        div[data-testid="stChatInput"] label,
        div[data-testid="stChatInput"] div[data-baseweb="base-input"] {
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #111827 !important;
        }

        div[data-testid="stChatInput"] textarea {
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #111827 !important;
            -webkit-text-fill-color: #111827 !important;
            caret-color: #111827 !important;
            font-size: 0.86rem !important;
            line-height: 1.25 !important;
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: #64748b !important;
            -webkit-text-fill-color: #64748b !important;
            opacity: 1 !important;
        }

        div[data-testid="stChatInput"] button {
            background-color: #005691 !important;
            border-radius: 50% !important;
            width: 32px !important;
            height: 32px !important;
            min-width: 32px !important;
            margin-right: 4px !important;
            padding: 6px !important;
        }

        div[data-testid="stChatInput"] button svg {
            fill: #ffffff !important;
            color: #ffffff !important;
            width: 17px !important;
            height: 17px !important;
        }

        hr {
            margin: 0.35rem 0 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 🔐 [인증] 로그인 로직
# ============================================================
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"):
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)

        st.markdown(
            f"<h3 style='text-align:center; color:#003366; font-weight:800; margin-bottom:20px;'>{SYSTEM_NAME}</h3>",
            unsafe_allow_html=True
        )

        pwd = st.text_input(
            "보안 코드 입력",
            type="password",
            placeholder="코드를 입력하세요",
            label_visibility="collapsed"
        )

        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        elif pwd:
            st.error("❌ 보안 코드가 일치하지 않습니다.")

    st.stop()

# ============================================================
# 🧠 [엔진] DB 로드
# ============================================================
@st.cache_resource
def load_intelligent_db():
    if not os.path.exists("faiss_index_saved"):
        return None, "faiss_index_saved 데이터가 없습니다."

    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=random.choice(API_KEYS)
        )

        vdb = FAISS.load_local(
            "faiss_index_saved",
            embeddings,
            allow_dangerous_deserialization=True
        )

        return vdb, None

    except Exception as e:
        return None, f"데이터베이스 로드 실패: {e}"


vdb, db_status_msg = load_intelligent_db()

if not vdb:
    st.error(f"🚨 엔진 가동 실패: {db_status_msg}")
    st.stop()


def get_intelligent_response(prompt_text):
    time.sleep(1.0)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=random.choice(API_KEYS),
        temperature=0.0
    )

    for chunk in llm.stream(prompt_text):
        if chunk.content:
            yield chunk.content


# ============================================================
# 🏥 로고 Base64 처리
# ============================================================
logo_html = ""

if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}'>"

# ============================================================
# 🧭 상단 배너
# ============================================================
st.markdown(f"""
<div class='dashboard-header'>
    {logo_html}
    <h1>{SYSTEM_NAME}</h1>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 🧩 모드 선택
# ============================================================
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "🔍 인증 지침서 검색"

st.session_state.current_mode = st.radio(
    "모드 선택",
    ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"],
    horizontal=True,
    label_visibility="collapsed"
)

mode = st.session_state.current_mode

if "search_msgs" not in st.session_state:
    st.session_state.search_msgs = []

if "train_msgs" not in st.session_state:
    st.session_state.train_msgs = []

if "current_q" not in st.session_state:
    st.session_state.current_q = None

quick_query = None

# ============================================================
# 📌 AI 답변 시스템 룰
# ============================================================
SYS_RULE = f"""당신은 '{SYSTEM_NAME}'입니다.
사용자의 질문에 대해 반드시 제공된 [원문 데이터]를 분석하여 아래의 3단 구조 양식에 맞춰 답변하십시오.

### 💡 답변 요약
(질문에 대한 핵심 내용을 2~3줄로 명확하게 요약)

### ⚖️ 근거
(답변의 근거가 되는 지침서 항목과 **정확한 페이지 번호**를 불릿 기호(•)를 사용하여 나열. 예: • 환자안전 지침서 3.4 (p.12))
🚨 주의사항: 근거 작성 시 절대로 영문 파일명(예: guide.pdf 등)을 출력하지 마십시오. 오직 한글 지침서 이름과 (p.00) 형태의 페이지만 표기하십시오.

### 📂 예상 확인자료
(현장 평가 시 확인하거나 준비해야 할 관련 기록지, 보고서, 체크리스트 등을 불릿 기호(•)를 사용하여 나열)
"""

# ============================================================
# 📐 메인 레이아웃
# ============================================================
main_col, answer_col = st.columns([2.2, 1], gap="large")

with main_col:

    if mode == "🔍 인증 지침서 검색":

        welcome_col, quick_col = st.columns([1, 1], gap="medium")

        with welcome_col:
            st.markdown(f"""
            <div class='welcome-section'>
                <h2>안녕하세요! {SYSTEM_NAME}입니다</h2>
                <p>방대한 인증 지침서를 단 몇 초 만에 검색하고, AI 감독관과 함께 실전 훈련을 진행하세요. 지침 기반의 정확한 답변과 근거 페이지를 즉시 확인하시고 평가를 대비하십시오.</p>
            </div>
            """, unsafe_allow_html=True)

        with quick_col:
            st.markdown("""
            <div class='quick-card'>
                <div class='quick-prompts-title'>💡 이렇게 질문해 보세요</div>
            """, unsafe_allow_html=True)

            q1, q2 = st.columns(2)

            with q1:
                if st.button("💬 낙상 보고 절차", use_container_width=True):
                    quick_query = "낙상 발생 시 보고 절차와 타임라인은 어떻게 되나요?"

                if st.button("💬 감염관리 위원회", use_container_width=True):
                    quick_query = "감염관리 위원회의 구성 요건과 주요 역할은 무엇인가요?"

                if st.button("💬 CPR 이수 기준", use_container_width=True):
                    quick_query = "직원의 심폐소생술(CPR) 교육 이수 기준과 유효기간은?"

            with q2:
                if st.button("💬 근접오류 보고", use_container_width=True):
                    quick_query = "근접오류(Near Miss) 정의와 보고 활성화 방안은?"

                if st.button("💬 병동 환경 점검", use_container_width=True):
                    quick_query = "병동 환경 점검 체크리스트 필수 항목을 알려주세요."

                if st.button("💬 화재 R.A.C.E.", use_container_width=True):
                    quick_query = "화재 발생 시 상황별 대응 매뉴얼(R.A.C.E.) 내용을 요약해줘."

            st.markdown("</div>", unsafe_allow_html=True)

        st.write("<br>", unsafe_allow_html=True)

        for m in st.session_state.search_msgs:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

    elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":

        st.markdown(f"""
        <div class='welcome-section'>
            <h2>실전 모의감독관 훈련</h2>
            <p>AI 감독관이 인증 지침서 기반 질문을 생성하고, 입력하신 답변을 기준으로 보완점을 제시합니다.</p>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡 하단의 채팅창에 답변을 입력하면 AI가 지침서 기반으로 채점합니다.")

        if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
            with st.chat_message("assistant"):
                with st.spinner("💭 감독관이 지침서를 분석하여 질문을 생성 중..."):
                    random_docs = vdb.similarity_search(
                        random.choice(["지침", "규정"]),
                        k=3
                    )

                    ctx_list = []

                    for d in random_docs:
                        p_val = d.metadata.get("page", "")
                        p_num = f"{p_val + 1}" if isinstance(p_val, int) else str(p_val)
                        ctx_list.append(f"[페이지: p.{p_num}]\\n{d.page_content}")

                    sample_ctx = "\\n\\n".join(ctx_list)

                    q_stream = get_intelligent_response(
                        f"인증평가 감독관 질문 1개 생성. 실제 현장에서 직원의 지침 숙지 여부를 묻는 날카로운 질문을 하세요.\\n내용:\\n{sample_ctx}"
                    )

                    st.session_state.current_q = st.write_stream(q_stream)
                    st.session_state.train_msgs.append({
                        "role": "assistant",
                        "content": st.session_state.current_q
                    })

        for m in st.session_state.train_msgs:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])

# ============================================================
# 📌 우측 AI 표준 답변 가이드
# ============================================================
with answer_col:
    st.markdown("""
    <div class='answer-structure'>
        <h3>🌟 AI 표준 답변 가이드</h3>
        <ul>
            <li>
                <div class='answer-structure-title'>💡 답변 요약</div>
                <div class='answer-structure-content'>핵심 내용을 2~3줄로 명확하게 요약하여 먼저 제시합니다.</div>
            </li>
            <li>
                <div class='answer-structure-title'>⚖️ 근거</div>
                <div class='answer-structure-content'>• 관련 지침서 항목<br>• 5주기 인증기준 번호<br>• 정확한 지침서 페이지 번호</div>
            </li>
            <li>
                <div class='answer-structure-title'>📂 예상 확인자료</div>
                <div class='answer-structure-content'>현장에서 요구될 가능성이 높은 규정, 기록지, 보고서, 체크리스트를 제시합니다.</div>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 💬 채팅 입력 처리
# ============================================================
chat_input_query = st.chat_input("인증 지침에 관해 질문하거나 감독관의 질문에 답변하십시오...")

final_query = chat_input_query or quick_query

if final_query:

    if mode == "🔍 인증 지침서 검색":

        st.session_state.search_msgs.append({
            "role": "user",
            "content": final_query
        })

        with st.chat_message("user"):
            st.markdown(final_query)

        with st.chat_message("assistant"):
            with st.spinner("💭 지침서를 분석하며 답변을 정리 중..."):
                try:
                    docs = vdb.similarity_search(final_query, k=15)

                    ctx_list = []

                    for d in docs:
                        p_val = d.metadata.get("page", "")
                        p_num = f"{p_val + 1}" if isinstance(p_val, int) else str(p_val)
                        ctx_list.append(f"[페이지: p.{p_num}]\\n{d.page_content}")

                    ctx_str = "\\n\\n".join(ctx_list)

                    full_ans = st.write_stream(
                        get_intelligent_response(
                            f"{SYS_RULE}\\n\\n[원문 데이터]\\n{ctx_str}\\n\\n질문: {final_query}"
                        )
                    )

                    st.session_state.search_msgs.append({
                        "role": "assistant",
                        "content": full_ans
                    })

                except Exception as e:
                    st.error(f"🚨 오류: {e}")

    else:

        if st.session_state.current_q:

            st.session_state.train_msgs.append({
                "role": "user",
                "content": final_query
            })

            with st.chat_message("user"):
                st.markdown(final_query)

            with st.chat_message("assistant"):
                with st.spinner("💭 답변을 기반으로 지침서 부합 여부 채점 중..."):
                    try:
                        docs = vdb.similarity_search(
                            st.session_state.current_q,
                            k=10
                        )

                        ctx_list = []

                        for d in docs:
                            p_val = d.metadata.get("page", "")
                            p_num = f"{p_val + 1}" if isinstance(p_val, int) else str(p_val)
                            ctx_list.append(f"[페이지: p.{p_num}]\\n{d.page_content}")

                        ctx_str = "\\n\\n".join(ctx_list)

                        full_ans = st.write_stream(
                            get_intelligent_response(
                                f"인증평가 감독관 시선에서 직원의 답변 채점 및 보완. 실제 지침서 내용 기반 피드백. 파일명(guide.pdf 등) 절대 출력 금지.\\n질문: {st.session_state.current_q}\\n직원 답변: {final_query}\\n지침 데이터:\\n{ctx_str}"
                            )
                        )

                        st.session_state.train_msgs.append({
                            "role": "assistant",
                            "content": full_ans
                        })

                        st.session_state.current_q = None

                    except Exception as e:
                        st.error(f"🚨 오류: {e}")
