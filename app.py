import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
import random
import time
import base64
import re

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
# 🎨 [디자인] PC 원본 유지 + 모바일 전용 보정
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    :root { color-scheme: light !important; }

    html, body {
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

    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        margin-bottom: 12px !important;
    }


    /* 답변 생성 중 Streamlit이 이전 화면을 흐리게 남기는 stale element 숨김 */
    div[data-testid="staleElement"],
    div[data-testid="staleElement"] *,
    .stale-element,
    .stale-element *,
    [data-stale="true"],
    [data-stale="true"] * {
        opacity: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* 새 질문/생각중/답변을 입력창 가까운 아래쪽으로 내려보내는 공간 */
    .latest-chat-spacer {
        height: clamp(140px, 28vh, 360px);
        width: 100%;
    }

    /* ============================================================ */
    /* 🖥️ PC 화면 */
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

    .dashboard-header * { color: #ffffff !important; }

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
        padding: 35px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 25px;
        margin-bottom: 30px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    .welcome-section img {
        height: 75px !important;
        flex-shrink: 0;
    }

    .welcome-section h2 {
        color: #111827 !important;
        margin: 0 0 10px 0;
        font-size: 1.6rem !important;
        font-weight: 800;
    }

    .welcome-section p {
        color: #475569 !important;
        margin: 0;
        font-size: 1.05rem !important;
        line-height: 1.6;
    }

    .quick-prompts-title {
        margin: 0 0 15px 0;
        font-size: 1.2rem !important;
        color: #1e293b !important;
        font-weight: 800;
    }

    div[data-testid="stButton"] button {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 25px !important;
        color: #005691 !important;
        font-weight: 600 !important;
        padding: 12px 20px !important;
        display: flex !important;
        justify-content: center !important;
        text-align: center !important;
        width: 100% !important;
        transition: all 0.2s ease-in-out;
        font-size: 0.95rem !important;
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


    .verified-reference-box {
        margin-top: 20px;
        padding: 16px 18px;
        background: #ffffff;
        border: 1px solid #dbe3ef;
        border-left: 5px solid #005691;
        border-radius: 12px;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04);
    }

    .verified-reference-box h4 {
        margin: 0 0 10px 0;
        color: #003366 !important;
        font-size: 1.05rem !important;
        font-weight: 800;
    }

    .verified-reference-box ul {
        margin: 0;
        padding-left: 20px;
    }

    .verified-reference-box li {
        color: #334155 !important;
        margin-bottom: 6px;
        font-size: 0.95rem;
        line-height: 1.45;
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
    /* 📱 모바일 화면 */
    /* ============================================================ */
    @media (max-width: 768px) {
        :root, html, body {
            color-scheme: light !important;
            background: #f8f9fa !important;
            background-color: #f8f9fa !important;
        }

        html, body,
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
            padding-bottom: 6rem !important;
            overflow-x: hidden !important;
        }

        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            display: block !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.35rem !important;
        }

        .dashboard-header {
            min-height: 52px !important;
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

        .welcome-section {
            padding: 10px 12px !important;
            margin-bottom: 6px !important;
            border-radius: 10px !important;
            min-height: auto !important;
            background-color: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04) !important;
            display: block !important;
        }

        .welcome-section img { display: none !important; }

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

        .welcome-section br { display: none !important; }

        .quick-prompts-title {
            font-size: 0.86rem !important;
            line-height: 1.15 !important;
            margin: 2px 0 5px 0 !important;
            font-weight: 800 !important;
            letter-spacing: -0.4px !important;
        }

        div[data-testid="stButton"] { margin-bottom: 2px !important; }

        div[data-testid="stButton"] button {
            min-height: 30px !important;
            height: 30px !important;
            padding: 4px 8px !important;
            border-radius: 15px !important;
            font-size: 0.7rem !important;
            line-height: 1.1 !important;
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
            font-size: 0.7rem !important;
            line-height: 1.1 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        div[data-testid="stButton"] button:hover {
            transform: none !important;
            box-shadow: none !important;
        }

        div[class*="st-key-q_infection"],
        div[class*="st-key-q_cpr"],
        div[class*="st-key-q_nearmiss"],
        div[class*="st-key-q_ward"] {
            display: none !important;
        }

        .answer-structure {
            padding: 9px 10px !important;
            margin-top: 2px !important;
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
            min-height: 56px !important;
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
            line-height: 1.2 !important;
            color: #475569 !important;
            word-break: keep-all !important;
            letter-spacing: -0.25px !important;
        }

        .answer-structure-content br { display: none !important; }


        .verified-reference-box {
            margin-top: 12px !important;
            padding: 11px 13px !important;
            border-radius: 10px !important;
        }

        .verified-reference-box h4 {
            font-size: 0.88rem !important;
            margin-bottom: 7px !important;
        }

        .verified-reference-box li {
            font-size: 0.76rem !important;
            line-height: 1.35 !important;
        }

        .element-container { margin-bottom: 0.22rem !important; }


        .latest-chat-spacer {
            height: clamp(90px, 18vh, 190px) !important;
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

        hr { margin: 0.35rem 0 !important; }
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
def load_intelligent_dbs():
    """
    인덱스 2개 로드:
    - faiss_index_saved : 지침서 + 핸드북 전체 인덱스 / 정밀검증·모의훈련용
    - faiss_index_guide : 지침서 전용 인덱스 / 빠른검색용
    """
    if not os.path.exists("faiss_index_saved"):
        return None, None, "faiss_index_saved 데이터가 없습니다."

    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=random.choice(API_KEYS)
        )

        vdb_all = FAISS.load_local(
            "faiss_index_saved",
            embeddings,
            allow_dangerous_deserialization=True
        )

        vdb_guide = None

        if os.path.exists("faiss_index_guide"):
            try:
                vdb_guide = FAISS.load_local(
                    "faiss_index_guide",
                    embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as guide_error:
                # 지침서 전용 인덱스 로드 실패 시 전체 인덱스로 fallback
                vdb_guide = None
                print(f"faiss_index_guide 로드 실패, 전체 인덱스로 대체: {guide_error}")

        if vdb_guide is None:
            vdb_guide = vdb_all

        return vdb_all, vdb_guide, None

    except Exception as e:
        return None, None, f"데이터베이스 로드 실패: {e}"


vdb, guide_vdb, db_status_msg = load_intelligent_dbs()

if not vdb:
    st.error(f"🚨 엔진 가동 실패: {db_status_msg}")
    st.stop()


def make_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=random.choice(API_KEYS),
        temperature=0.0
    )


def get_intelligent_response(prompt_text):
    time.sleep(0.5)
    llm = make_llm()

    for chunk in llm.stream(prompt_text):
        if chunk.content:
            yield chunk.content


def get_intelligent_text(prompt_text):
    time.sleep(0.5)
    llm = make_llm()
    result = llm.invoke(prompt_text)
    return result.content if hasattr(result, "content") else str(result)


# ============================================================
# 📌 검색 보강 설정
# ============================================================
VECTOR_K = 30
EXACT_LIMIT = 20
FINAL_DOC_LIMIT = 18
GUIDE_PAGE_OFFSET = 0  # 새 코랩 인덱스는 printed_page가 정확히 저장되므로 지침서 페이지 보정 없음

# ============================================================
# 📌 metadata 기반 출처/페이지 처리
# ============================================================
def get_raw_source_from_doc(d):
    meta = getattr(d, "metadata", {}) or {}

    raw_source = (
        meta.get("source")
        or meta.get("file_path")
        or meta.get("filename")
        or meta.get("file_name")
        or meta.get("doc_name")
        or meta.get("title")
        or ""
    )

    return os.path.basename(str(raw_source)).strip()


def get_source_label(d):
    raw_source = get_raw_source_from_doc(d)
    source_lower = raw_source.lower()

    if "manual2" in source_lower or "manual" in source_lower:
        return "핸드북"

    if "guide" in source_lower:
        return "지침서"

    return "자료"


def normalize_page_number_for_compare(page_value):
    """
    비교용 페이지 번호 정규화:
    - 089, 89, p.089, 089페이지를 모두 '89'로 통일
    - 숫자가 아닌 라벨은 원문을 유지
    """
    if page_value is None or page_value == "":
        return None

    text = str(page_value).strip()
    text = text.replace("p.", "").replace("P.", "")
    text = text.replace("페이지", "").strip()

    if text.isdigit():
        return str(int(text))

    return text


def format_page_number_for_display(page_value):
    """
    화면 출력용 페이지 번호:
    - 핸드북처럼 008, 089 형태가 들어온 경우 3자리 유지
    - 숫자 89처럼 들어온 경우 89로 표시
    """
    if page_value is None or page_value == "":
        return None

    raw = str(page_value).strip()
    cleaned = raw.replace("p.", "").replace("P.", "")
    cleaned = cleaned.replace("페이지", "").strip()

    if cleaned.isdigit():
        # 원본이 3자리 이상 0으로 시작하면 그대로 유지: 008, 089
        if len(cleaned) >= 3 and cleaned.startswith("0"):
            return cleaned
        return str(int(cleaned))

    return cleaned


def extract_page_number(page_value):
    """
    metadata에서 페이지 번호를 꺼낼 때 사용하는 기본 함수.
    비교용이 아니라 '원본 표시값'을 최대한 보존합니다.
    """
    return format_page_number_for_display(page_value)


def get_doc_page(d):
    meta = getattr(d, "metadata", {}) or {}

    raw_page = None

    if meta.get("printed_page") is not None:
        raw_page = meta.get("printed_page")
    elif meta.get("display_page") is not None:
        raw_page = meta.get("display_page")
    elif meta.get("page_label") is not None:
        raw_page = meta.get("page_label")
    elif meta.get("page") is not None:
        raw_page = meta.get("page")
    elif meta.get("page_number") is not None:
        raw_page = meta.get("page_number")
    elif meta.get("p") is not None:
        raw_page = meta.get("p")

    page = extract_page_number(raw_page)

    if page is None:
        return None

    # 지침서 guide 파일은 실제 하단 페이지보다 +4 크게 저장된 상태로 보고 -4 보정
    # 새로 만든 인덱스가 이미 printed_page를 정확히 담고 있다면 GUIDE_PAGE_OFFSET 값을 0으로 바꾸면 됩니다.
    if get_source_label(d) == "지침서":
        try:
            return str(max(1, int(normalize_page_number_for_compare(page)) + GUIDE_PAGE_OFFSET))
        except Exception:
            return page

    return page


def get_doc_ref_label(d):
    source_label = get_source_label(d)
    page = get_doc_page(d)

    if page is None:
        return f"{source_label} 페이지 정보 없음"

    return f"{source_label} p.{page}"


def build_allowed_refs(docs, max_refs=12, max_per_source=6):
    """
    AI가 최종 근거 페이지를 고를 수 있도록 후보 페이지를 넉넉하게 제공합니다.
    실제 화면 표시는 select_verified_refs_by_ai()에서 선택된 최소 1개~최대 4개만 합니다.
    """
    refs = []
    seen = set()
    source_counts = {
        "핸드북": 0,
        "지침서": 0,
        "자료": 0
    }

    for d in docs:
        source_label = get_source_label(d)
        ref = get_doc_ref_label(d)

        if "페이지 정보 없음" in ref:
            continue

        if ref in seen:
            continue

        if source_counts.get(source_label, 0) >= max_per_source:
            continue

        seen.add(ref)
        refs.append(ref)
        source_counts[source_label] = source_counts.get(source_label, 0) + 1

        if len(refs) >= max_refs:
            break

    return refs


def build_verified_reference_html(allowed_refs, max_refs=4):
    """
    AI 답변과 분리하여 코드가 직접 근거 페이지를 표시합니다.
    페이지 번호가 AI 답변에서 지워지는 문제를 방지하기 위한 강제 표출 영역입니다.
    """
    if not allowed_refs:
        return ""

    clean_refs = []
    seen = set()

    for ref in allowed_refs:
        if not ref:
            continue

        # manual/guide 등 내부 파일명 노출 방지
        ref = remove_file_names_and_forbidden_words(str(ref)).strip()
        ref = re.sub(r"\(\s*\)", "", ref).strip()

        if not ref:
            continue

        # 핸드북 p.89가 들어오면 핸드북 p.089 허용목록 표기값은 그대로 유지
        if ref not in seen:
            seen.add(ref)
            clean_refs.append(ref)

        if len(clean_refs) >= max_refs:
            break

    if not clean_refs:
        return ""

    lis = "\n".join([f"<li>{r}</li>" for r in clean_refs])

    return f"""
<div class='verified-reference-box'>
    <h4>📌 확인된 근거 페이지</h4>
    <ul>
        {lis}
    </ul>
</div>
"""


def build_context_for_ai(docs):
    ctx_list = []

    for idx, d in enumerate(docs, start=1):
        ref_label = get_doc_ref_label(d)
        content = d.page_content

        ctx_list.append(
            f"[근거자료 {idx} / 허용 근거표기: {ref_label}]\n{content}"
        )

    return "\n\n".join(ctx_list)


def group_docs_by_ref(docs):
    """
    근거표기별로 실제 원문 조각을 묶습니다.
    예: '핸드북 p.089' -> 해당 페이지 chunk들
    """
    grouped = {}

    for d in docs:
        ref = get_doc_ref_label(d)
        if "페이지 정보 없음" in ref:
            continue

        content = getattr(d, "page_content", "") or ""
        if not content.strip():
            continue

        grouped.setdefault(ref, [])
        grouped[ref].append(content[:1200])

    return grouped


def build_reference_selection_context(docs, allowed_refs):
    """
    AI가 근거 페이지를 고를 수 있도록 후보 페이지별 원문 조각을 구성합니다.
    """
    grouped = group_docs_by_ref(docs)
    blocks = []

    for ref in allowed_refs:
        chunks = grouped.get(ref, [])
        if not chunks:
            continue

        joined = "\n---\n".join(chunks[:2])
        blocks.append(f"[{ref}]\n{joined}")

    return "\n\n".join(blocks)


def parse_selected_refs(raw_text, allowed_refs, max_total=4, max_per_source=2):
    """
    AI가 반환한 텍스트에서 허용된 근거표기만 추출합니다.
    089/89 차이를 정규화해서 매칭합니다.
    """
    if not raw_text:
        return []

    allowed_map = {}
    for ref in allowed_refs:
        m = re.search(r"(핸드북|지침서)\s*p\.\s*([0-9]+)", ref)
        if not m:
            continue
        source = m.group(1)
        num = normalize_page_number_for_compare(m.group(2))
        allowed_map[(source, num)] = ref

    found = []
    seen = set()
    source_counts = {"핸드북": 0, "지침서": 0}

    for m in re.finditer(r"(핸드북|지침서)\s*p\.\s*([0-9]+)", raw_text):
        source = m.group(1)
        num = normalize_page_number_for_compare(m.group(2))
        key = (source, num)

        if key not in allowed_map:
            continue

        ref = allowed_map[key]

        if ref in seen:
            continue

        if source_counts.get(source, 0) >= max_per_source:
            continue

        seen.add(ref)
        found.append(ref)
        source_counts[source] = source_counts.get(source, 0) + 1

        if len(found) >= max_total:
            break

    return found


def fallback_select_refs_by_keyword(query, docs, allowed_refs, max_total=2):
    """
    AI 선택 실패 시 키워드 점수 기반으로 최소 근거를 선택합니다.
    """
    grouped = group_docs_by_ref(docs)
    scored = []

    for ref in allowed_refs:
        joined = "\n".join(grouped.get(ref, []))
        score = keyword_score(query, type("TempDoc", (), {"page_content": joined})())
        scored.append((score, ref))

    scored.sort(key=lambda x: x[0], reverse=True)

    selected = []
    for score, ref in scored:
        if score <= 0 and selected:
            continue
        if ref not in selected:
            selected.append(ref)
        if len(selected) >= max_total:
            break

    return selected


def select_verified_refs_by_ai(query, docs, allowed_refs):
    """
    최종 답변 전에 AI가 실제 원문 조각을 보고 관련 페이지를 고릅니다.
    화면에는 이 함수가 고른 페이지만 표시합니다.
    """
    if not allowed_refs:
        return []

    selection_context = build_reference_selection_context(docs, allowed_refs)

    if not selection_context.strip():
        return []

    prompt = f"""
너는 병원 인증자료 근거 페이지 선별자입니다.

사용자 질문과 후보 페이지 원문을 비교해서, 답변 근거로 실제 관련 내용이 들어있는 페이지 번호만 고르십시오.

규칙:
- 반드시 [허용 근거표기 목록]에 있는 표기만 선택하십시오.
- 핸드북은 최대 2개, 지침서는 최대 2개까지만 선택하십시오.
- 전체는 최대 4개까지만 선택하십시오.
- 직접 관련성이 가장 높은 페이지를 우선 선택하십시오.
- 관련성이 낮은 목차 페이지, 주변 페이지, 단순 유사어 페이지는 제외하십시오.
- 답은 설명 없이 근거표기만 줄바꿈으로 출력하십시오.
- 예: 핸드북 p.089

[사용자 질문]
{query}

[허용 근거표기 목록]
{", ".join(allowed_refs)}

[후보 페이지 원문]
{selection_context}
"""

    try:
        raw = get_intelligent_text(prompt)
        selected = parse_selected_refs(raw, allowed_refs, max_total=4, max_per_source=2)
    except Exception:
        selected = []

    if not selected:
        selected = fallback_select_refs_by_keyword(query, docs, allowed_refs, max_total=2)

    return selected



# ============================================================
# 🔍 검색 보강 로직: 벡터검색 + 정확문구/키워드 포함 후보
# ============================================================
def normalize_text(s):
    if not s:
        return ""
    s = str(s)
    s = re.sub(r"\s+", "", s)
    s = s.lower()
    return s


def get_query_terms(query):
    terms = re.findall(r"[가-힣A-Za-z0-9]{2,}", str(query))
    stopwords = {
        "알려줘", "어떻게", "되나요", "무엇인가요", "기준", "관련", "대한",
        "절차", "요약", "설명", "질문", "확인", "있는지"
    }
    return [t for t in terms if t not in stopwords]


@st.cache_resource
def get_all_faiss_docs():
    docs = []
    try:
        store = getattr(vdb, "docstore", None)
        if store is not None and hasattr(store, "_dict"):
            docs = list(store._dict.values())
    except Exception:
        docs = []
    return docs


def keyword_score(query, doc):
    q_norm = normalize_text(query)
    text = getattr(doc, "page_content", "") or ""
    t_norm = normalize_text(text)

    score = 0

    # 사용자가 원문 일부를 그대로 넣은 경우를 강하게 우선
    if q_norm and q_norm in t_norm:
        score += 100

    # 원문에서 공백 제외 8자 이상 연속 구간 일부가 들어간 경우
    if len(q_norm) >= 8:
        for n in [16, 12, 8]:
            for i in range(0, max(1, len(q_norm) - n + 1)):
                piece = q_norm[i:i+n]
                if len(piece) >= 8 and piece in t_norm:
                    score += n * 2
                    break

    # 키워드 포함 점수
    for term in get_query_terms(query):
        term_norm = normalize_text(term)
        if term_norm and term_norm in t_norm:
            score += 8

    return score


def exact_keyword_candidates(query, limit=EXACT_LIMIT):
    all_docs = get_all_faiss_docs()
    scored = []

    for d in all_docs:
        s = keyword_score(query, d)
        if s > 0:
            scored.append((s, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:limit]]


def doc_identity(d):
    meta = getattr(d, "metadata", {}) or {}
    page = get_doc_page(d)
    src = get_raw_source_from_doc(d)
    content = (getattr(d, "page_content", "") or "")[:120]
    return f"{src}|{page}|{content}"


def merge_unique_docs(*doc_groups):
    merged = []
    seen = set()

    for group in doc_groups:
        for d in group:
            key = doc_identity(d)
            if key not in seen:
                seen.add(key)
                merged.append(d)

    return merged



def collect_fast_guide_docs(query, k=6):
    """
    빠른검색 전용:
    - faiss_index_guide 지침서 전용 인덱스만 검색
    - 후보 k=6으로 제한
    - 보강검색 제거
    - 페이지 검증/정밀검증 없음
    """
    docs = []

    try:
        first = guide_vdb.similarity_search(query, k=k)
        filtered = [d for d in first if get_source_label(d) == "지침서"]
        docs.extend(filtered if filtered else first)
    except Exception:
        pass

    unique = []
    seen = set()

    for d in docs:
        key = doc_identity(d)
        if key not in seen:
            seen.add(key)
            unique.append(d)

    return unique[:k]


def build_fast_context_for_ai(docs):
    """
    빠른검색용 원문 데이터:
    - 페이지/파일명 노출 금지
    - 지침서 내용 조각만 전달
    - 조각당 900자로 제한하여 속도 개선
    """
    ctx_list = []

    for idx, d in enumerate(docs, start=1):
        content = getattr(d, "page_content", "") or ""
        content = content[:900]
        ctx_list.append(f"[지침서 근거자료 {idx}]\n{content}")

    return "\n\n".join(ctx_list)


FAST_SYS_RULE = """당신은 '검단탑병원 인증 AI 시스템'입니다.

사용자의 질문에 대해 제공된 [지침서 원문 데이터]만 근거로 답변하십시오.
빠른검색 모드이므로 페이지 번호는 절대 작성하지 마십시오.
파일명, manual, guide, pdf, hwp 같은 표현도 절대 출력하지 마십시오.

답변은 반드시 아래 3단 구조로 작성하십시오.

### 💡 답변 요약
- 질문에 대한 핵심 내용을 2~3줄로 간결하게 요약하십시오.

### ⚖️ 근거
- 지침서에서 확인되는 관련 기준, 절차, 조사방법을 간결하게 설명하십시오.
- 페이지 번호는 쓰지 마십시오.
- 원문 데이터에 없는 내용은 단정하지 마십시오.
- 불필요한 장문 설명은 피하십시오.

### 📂 예상 확인자료
- 현장 평가 시 확인하거나 준비해야 할 규정, 기록지, 보고서, 체크리스트 등을 핵심만 불릿 기호로 제시하십시오.
"""


def collect_candidate_docs(query):
    """
    1) FAISS 벡터 검색 k=30
    2) 전체 docstore에서 정확문구/키워드 포함 후보 보강
    3) 키워드 점수 + 벡터검색 순서를 섞어 최종 후보 축소
    """
    vector_docs = vdb.similarity_search(query, k=VECTOR_K)
    exact_docs = exact_keyword_candidates(query, limit=EXACT_LIMIT)

    merged = merge_unique_docs(exact_docs, vector_docs)

    scored = []
    for idx, d in enumerate(merged):
        s = keyword_score(query, d)
        # exact 후보를 앞에 둔 효과 + 기존 순서 보존
        score = s - (idx * 0.01)
        scored.append((score, idx, d))

    scored.sort(key=lambda x: x[0], reverse=True)

    final_docs = [d for _, _, d in scored[:FINAL_DOC_LIMIT]]

    # 점수가 낮아도 벡터검색 상위 일부는 안전하게 포함
    final_docs = merge_unique_docs(final_docs, vector_docs[:8])

    return final_docs[:FINAL_DOC_LIMIT]


# ============================================================
# 🧹 출력 보정
# ============================================================
def remove_file_names_and_forbidden_words(text):
    if not text:
        return ""

    cleaned = text

    forbidden_patterns = [
        r"\bmanual\d*\b\s*/?\s*",
        r"\bguide\d*\b\s*/?\s*",
        r"\b[a-zA-Z0-9_\-]+\.(pdf|PDF|hwp|HWP|docx|DOCX|txt|TXT)\b",
        r"파일명\s*[:：]?\s*[^\n]+",
        r"출처\s*[:：]?\s*(manual\d*|guide\d*)",
    ]

    for pattern in forbidden_patterns:
        cleaned = re.sub(pattern, "", cleaned)

    cleaned = cleaned.replace("manual2", "")
    cleaned = cleaned.replace("manual", "")
    cleaned = cleaned.replace("guide", "")

    return cleaned.strip()



def strip_page_refs_from_ai_answer(text):
    """
    AI 답변 본문에서는 페이지 표기를 전부 제거합니다.
    실제 근거 페이지는 build_verified_reference_html()이 별도 박스로 표시합니다.
    """
    if not text:
        return ""

    cleaned = text

    # 핸드북 p.089 / 지침서 p.79 / p.89 / 89페이지 제거
    cleaned = re.sub(r"\((?:\s*(?:핸드북|지침서)\s*)?p\.\s*[0-9]+\s*\)", "", cleaned)
    cleaned = re.sub(r"(핸드북|지침서)\s*p\.\s*[0-9]+", "", cleaned)
    cleaned = re.sub(r"(?<![가-힣])p\.\s*[0-9]+", "", cleaned)
    cleaned = re.sub(r"[0-9]+\s*페이지", "", cleaned)

    # 빈 괄호 및 찌꺼기 제거
    cleaned = re.sub(r"\(\s*[,，]?\s*\)", "", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    cleaned = re.sub(r"（\s*）", "", cleaned)
    cleaned = re.sub(r"\s+\n", "\n", cleaned)

    return cleaned.strip()


def force_allowed_refs_only(text, allowed_refs):
    """
    답변 안의 근거표기를 허용 목록 기준으로 정리합니다.
    핵심 보정:
    - 허용 목록이 '핸드북 p.089'이고 AI가 '핸드북 p.89'라고 써도 같은 페이지로 인정
    - 허용 목록이 '지침서 p.79'이고 AI가 '지침서 p.079'라고 써도 같은 페이지로 인정
    - 파일명/manual/guide는 제거
    """
    if not text:
        return ""

    if not allowed_refs:
        return text

    # 비교용: ('핸드북', '89') -> 화면출력용 '핸드북 p.089'
    allowed_pair_to_display = {}
    allowed_page_to_display = {}

    for ref in allowed_refs:
        m = re.search(r"(핸드북|지침서)\s*p\.\s*([0-9]+)", ref)
        if m:
            source = m.group(1)
            raw_num = m.group(2)
            norm_num = normalize_page_number_for_compare(raw_num)
            display_num = format_page_number_for_display(raw_num)

            allowed_pair_to_display[(source, norm_num)] = f"{source} p.{display_num}"

            # p.번호만 나온 경우도 허용하되, 같은 번호가 여러 출처에 있으면 첫 번째 기준
            if norm_num not in allowed_page_to_display:
                allowed_page_to_display[norm_num] = f"p.{display_num}"

    def repl_full(match):
        source = match.group(1)
        raw_num = match.group(2)
        norm_num = normalize_page_number_for_compare(raw_num)
        key = (source, norm_num)

        if key in allowed_pair_to_display:
            return allowed_pair_to_display[key]

        return ""

    # 핸드북 p.089 / 핸드북 p.89 / 지침서 p.079 모두 처리
    text = re.sub(r"(핸드북|지침서)\s*p\.\s*([0-9]+)", repl_full, text)

    def repl_page_only(match):
        raw_num = match.group(1)
        norm_num = normalize_page_number_for_compare(raw_num)

        if norm_num in allowed_page_to_display:
            return allowed_page_to_display[norm_num]

        return ""

    # 출처 없이 p.089만 나온 경우
    text = re.sub(r"(?<![가-힣])p\.\s*([0-9]+)", repl_page_only, text)
    text = re.sub(r"([0-9]+)\s*페이지", lambda m: repl_page_only(m), text)

    # 빈 괄호 정리: () 또는 ( ) 제거
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"（\s*）", "", text)

    return text



# ============================================================
# 💬 대화 기록 표시: 최신 답변은 펼치고, 이전 대화는 접기
# ============================================================
def render_collapsed_chat_history(messages, expander_title="이전 대화 보기"):
    """
    기존 대화는 전부 expander 안에 접어서 보관합니다.
    새 질문/새 답변만 현재 화면에 표시해 이전 답변 잔상을 줄입니다.
    """
    if not messages:
        return

    with st.expander(f"💬 {expander_title}", expanded=False):
        for m in messages:
            role_label = "사용자" if m.get("role") == "user" else "AI"
            content = m.get("content", "")

            st.markdown(f"**{role_label}**")
            st.markdown(content, unsafe_allow_html=True)
            st.divider()


# ============================================================
# ✍️ 최신 답변 자리 고정 스트리밍 출력
# ============================================================
def stream_answer_in_current_chat_message(prompt_text, thinking_text="💭 생각 중입니다..."):
    """
    반드시 바깥의 with st.chat_message("assistant") 안에서만 호출합니다.
    로봇 아이콘 중복 없이 같은 AI 말풍선 안에서 생각중 → 답변 스트리밍을 수행합니다.
    """
    thinking_slot = st.empty()
    thinking_slot.markdown(f"**{thinking_text}**")

    streamed_text = st.write_stream(
        get_intelligent_response(prompt_text)
    )

    thinking_slot.empty()

    return streamed_text


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
    st.session_state.current_mode = "🔍 빠른검색 (예상 3~7초)"

st.session_state.current_mode = st.radio(
    "모드 선택",
    ["🔍 빠른검색 (예상 3~7초)", "🧪 정밀검증 (예상 15~40초)", "🕵️ 모의감독관 훈련 (예상 10~20초)"],
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

if "processing_new_query" not in st.session_state:
    st.session_state.processing_new_query = False

def mark_processing_new_query():
    st.session_state.processing_new_query = True

quick_query = None

# ============================================================
# 📌 AI 답변 시스템 룰
# ============================================================
SYS_RULE = f"""당신은 '{SYSTEM_NAME}'입니다.

사용자의 질문에 대해 반드시 제공된 [원문 데이터]만 근거로 답변하십시오.

답변은 반드시 아래 3단 구조로 작성하십시오.

### 💡 답변 요약
- 질문에 대한 핵심 내용을 2~3줄로 요약하십시오.

### ⚖️ 근거
- 관련 지침 내용과 기준을 설명하십시오.
- 페이지 번호는 절대 작성하지 마십시오.
- '핸드북 p.숫자', '지침서 p.숫자', 'p.숫자', '숫자페이지' 형식을 절대 출력하지 마십시오.
- 파일명, manual, guide, pdf, hwp 같은 표현은 절대 출력하지 마십시오.
- 실제 근거 페이지는 시스템 코드가 답변 하단에 자동으로 표시합니다.

### 📂 예상 확인자료
- 현장 평가 시 확인하거나 준비해야 할 기록지, 보고서, 체크리스트를 불릿 기호(•)로 제시하십시오.

금지사항:
- 파일명 출력 금지
- 영문 파일명 출력 금지
- manual2, manual, guide 출력 금지
- 모든 페이지 번호 생성 금지
- 원문 데이터에 없는 내용 단정 금지
"""

VERIFY_RULE = """
너는 병원 인증 지침 답변 검증자입니다.

아래 [초안 답변]을 [원문 데이터] 기준으로 검증하여 최종 답변으로 다시 작성하십시오.

반드시 수행할 검증:
1. 초안 답변의 각 주장 내용이 원문 데이터에 실제로 존재하는지 확인하십시오.
2. 사용자가 찾는 내용이 원문 데이터에 실제로 포함되어 있는지 검증하십시오.
3. 관련성이 낮거나 원문으로 확인되지 않는 내용은 삭제하십시오.
4. manual2, manual, guide, pdf, hwp, 파일명은 절대 출력하지 마십시오.
5. 페이지 번호는 절대 출력하지 마십시오.
6. '핸드북 p.숫자', '지침서 p.숫자', 'p.숫자', '숫자페이지' 형식을 절대 출력하지 마십시오.
7. 답변 형식은 반드시 아래 3단 구조를 유지하십시오.

### 💡 답변 요약
### ⚖️ 근거
### 📂 예상 확인자료

검증 후 최종 답변만 출력하십시오.
"""

# ============================================================
# 📐 PC 원래 구조: 왼쪽 본문 + 오른쪽 가이드
# ============================================================
main_col, answer_col = st.columns([2.2, 1], gap="large")

with main_col:

    st.markdown(f"""
    <div class='welcome-section'>
        {logo_html}
        <div>
            <h2>안녕하세요! {SYSTEM_NAME}입니다</h2>
            <p>방대한 인증 지침서를 단 몇 초 만에 검색하고, AI 감독관과 함께 실전 훈련을 진행하세요.<br>지침 기반의 정확한 답변과 근거 페이지를 즉시 확인하시고 평가를 완벽하게 대비하십시오.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if mode in ["🔍 빠른검색 (예상 3~7초)", "🧪 정밀검증 (예상 15~40초)"]:

        st.markdown(
            "<div class='quick-prompts-title'>💡 이렇게 질문해 보세요 (클릭 시 바로 검색됩니다)</div>",
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)

        with c1:
            if st.button("💬 낙상 발생 시 보고 절차를 알려줘", use_container_width=True, key="q_fall"):
                st.session_state.processing_new_query = True
                quick_query = "낙상 발생 시 보고 절차와 타임라인은 어떻게 되나요?"

            if st.button("💬 감염관리 위원회 구성 요건을 알려줘", use_container_width=True, key="q_infection"):
                st.session_state.processing_new_query = True
                quick_query = "감염관리 위원회의 구성 요건과 주요 역할은 무엇인가요?"

            if st.button("💬 직원의 CPR 이수 기준을 알려줘", use_container_width=True, key="q_cpr"):
                st.session_state.processing_new_query = True
                quick_query = "직원의 심폐소생술(CPR) 교육 이수 기준과 유효기간은?"

        with c2:
            if st.button("💬 화재 발생 시 R.A.C.E. 대응 절차를 알려줘", use_container_width=True, key="q_fire"):
                st.session_state.processing_new_query = True
                quick_query = "화재 발생 시 상황별 대응 매뉴얼(R.A.C.E.) 내용을 요약해줘."

            if st.button("💬 근접오류 보고 활성화 방법을 알려줘", use_container_width=True, key="q_nearmiss"):
                st.session_state.processing_new_query = True
                quick_query = "근접오류(Near Miss) 정의와 보고 활성화 방안은?"

            if st.button("💬 병동 환경 점검 필수 항목을 알려줘", use_container_width=True, key="q_ward"):
                st.session_state.processing_new_query = True
                quick_query = "병동 환경 점검 체크리스트 필수 항목을 알려주세요."

        st.write("<br>", unsafe_allow_html=True)

        render_collapsed_chat_history(
            st.session_state.search_msgs,
            expander_title="이전 검색 대화 보기"
        )

    elif mode == "🕵️ 모의감독관 훈련 (예상 10~20초)":

        st.info("💡 하단의 채팅창에 답변을 입력하면 AI가 지침서 기반으로 채점합니다.")

        if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True, key="new_training_question"):
            with st.chat_message("assistant"):
                with st.spinner("💭 감독관이 지침서를 분석하여 질문을 생성 중..."):
                    random_docs = vdb.similarity_search(
                        random.choice(["지침", "규정"]),
                        k=6
                    )

                    sample_ctx = build_context_for_ai(random_docs)

                    q_stream = get_intelligent_response(
                        f"인증평가 감독관 질문 1개 생성. 실제 현장에서 직원의 지침 숙지 여부를 묻는 날카로운 질문을 하세요. 파일명과 페이지 번호는 쓰지 마세요.\n\n내용:\n{sample_ctx}"
                    )

                    st.session_state.current_q = st.write_stream(q_stream)
                    st.session_state.train_msgs.append({
                        "role": "assistant",
                        "content": st.session_state.current_q
                    })

        render_collapsed_chat_history(
            st.session_state.train_msgs,
            expander_title="이전 훈련 대화 보기"
        )

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
                <div class='answer-structure-content'>관련 지침 내용과 기준을 설명하고, 검증된 핸드북/지침서 페이지를 표시합니다.</div>
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
chat_input_query = st.chat_input(
    "인증 지침에 관해 질문하거나 감독관의 질문에 답변하십시오...",
    key="main_chat_input",
    on_submit=mark_processing_new_query
)

final_query = chat_input_query or quick_query

if final_query:

    if mode in ["🔍 빠른검색 (예상 3~7초)", "🧪 정밀검증 (예상 15~40초)"]:

        st.session_state.search_msgs.append({
            "role": "user",
            "content": final_query
        })

        st.markdown("<div class='latest-chat-spacer'></div>", unsafe_allow_html=True)

        with st.chat_message("user"):
            st.markdown(final_query)

        # ------------------------------------------------------------
        # 🔍 빠른검색: 지침서만 / AI 1회 / 페이지 없음
        # ------------------------------------------------------------
        if mode == "🔍 빠른검색 (예상 3~7초)":
            with st.chat_message("assistant"):
                try:
                    status_slot = st.empty()
                    status_slot.markdown("**🔎 관련 지침을 찾는 중...**")

                    docs = collect_fast_guide_docs(final_query, k=6)
                    ctx_str = build_fast_context_for_ai(docs)

                    status_slot.empty()

                    if not docs:
                        fast_answer = """### 💡 답변 요약
- 지침서에서 질문과 직접 관련된 내용을 충분히 찾지 못했습니다.

### ⚖️ 근거
- 빠른검색은 지침서 일부 후보를 빠르게 확인하는 방식입니다.
- 정확한 근거 확인이 필요하면 정밀검증 모드를 사용해 주세요.

### 📂 예상 확인자료
- 관련 규정
- 관련 절차서
- 부서별 기록지 또는 체크리스트
"""
                        st.markdown(fast_answer)
                    else:
                        fast_answer = stream_answer_in_current_chat_message(
                            f"{FAST_SYS_RULE}\n\n[지침서 원문 데이터]\n{ctx_str}\n\n[사용자 질문]\n{final_query}",
                            thinking_text="💭 답변을 작성 중..."
                        )

                    fast_answer = remove_file_names_and_forbidden_words(fast_answer)
                    fast_answer = strip_page_refs_from_ai_answer(fast_answer)

                    st.session_state.search_msgs.append({
                        "role": "assistant",
                        "content": fast_answer
                    })
                    st.session_state.processing_new_query = False

                except Exception as e:
                    st.error(f"🚨 오류: {e}")
                    st.session_state.processing_new_query = False

        # ------------------------------------------------------------
        # 🧪 정밀검증: 지침서+핸드북 / 검증 / AI 페이지 선별
        # ------------------------------------------------------------
        else:
            with st.chat_message("assistant"):
                with st.spinner("💭 지침서와 핸드북을 넓게 검색하고 답변을 1차 작성 중..."):
                    try:
                        docs = collect_candidate_docs(final_query)

                        ctx_str = build_context_for_ai(docs)
                        allowed_refs = build_allowed_refs(docs, max_refs=12, max_per_source=6)

                        draft_answer = get_intelligent_text(
                            f"""
{SYS_RULE}

[원문 데이터]
{ctx_str}

[사용자 질문]
{final_query}
"""
                        )

                        with st.spinner("🔎 답변 내용과 근거 페이지를 AI가 재검증 중..."):
                            verified_answer = get_intelligent_text(
                                f"""
{VERIFY_RULE}

[원문 데이터]
{ctx_str}

[사용자 질문]
{final_query}

[초안 답변]
{draft_answer}
"""
                            )

                        verified_answer = remove_file_names_and_forbidden_words(verified_answer)
                        verified_answer = strip_page_refs_from_ai_answer(verified_answer)

                        selected_refs = select_verified_refs_by_ai(final_query, docs, allowed_refs)
                        reference_html = build_verified_reference_html(selected_refs, max_refs=4)
                        final_answer = verified_answer + "\n\n" + reference_html

                        st.markdown(verified_answer)
                        if reference_html:
                            st.markdown(reference_html, unsafe_allow_html=True)

                        st.session_state.search_msgs.append({
                            "role": "assistant",
                            "content": final_answer
                        })
                        st.session_state.processing_new_query = False

                    except Exception as e:
                        st.error(f"🚨 오류: {e}")
                        st.session_state.processing_new_query = False

    else:

        if st.session_state.current_q:

            st.session_state.train_msgs.append({
                "role": "user",
                "content": final_query
            })

            st.markdown("<div class='latest-chat-spacer'></div>", unsafe_allow_html=True)

            with st.chat_message("user"):
                st.markdown(final_query)

            with st.chat_message("assistant"):
                with st.spinner("💭 답변을 기반으로 지침서 부합 여부 채점 중..."):
                    try:
                        docs = collect_candidate_docs(st.session_state.current_q)

                        ctx_str = build_context_for_ai(docs)
                        allowed_refs = build_allowed_refs(docs, max_refs=12, max_per_source=6)

                        draft_answer = get_intelligent_text(
                            f"""
인증평가 감독관 시선에서 직원의 답변을 채점하고 보완점을 제시하십시오.

규칙:
- 실제 지침서 내용 기반으로만 피드백하십시오.
- 파일명은 출력하지 마십시오.
- manual2, manual, guide는 출력하지 마십시오.
- 페이지 번호는 절대 출력하지 마십시오.

[감독관 질문]
{st.session_state.current_q}

[직원 답변]
{final_query}

[지침 데이터]
{ctx_str}
"""
                        )

                        with st.spinner("🔎 채점 내용과 해당 페이지 근거를 AI가 재검증 중..."):
                            verified_answer = get_intelligent_text(
                                f"""
{VERIFY_RULE}

[원문 데이터]
{ctx_str}

[감독관 질문]
{st.session_state.current_q}

[직원 답변]
{final_query}

[초안 답변]
{draft_answer}
"""
                            )

                        verified_answer = remove_file_names_and_forbidden_words(verified_answer)
                        verified_answer = strip_page_refs_from_ai_answer(verified_answer)

                        selected_refs = select_verified_refs_by_ai(st.session_state.current_q, docs, allowed_refs)
                        reference_html = build_verified_reference_html(selected_refs, max_refs=4)
                        final_answer = verified_answer + "\n\n" + reference_html

                        st.markdown(verified_answer)
                        if reference_html:
                            st.markdown(reference_html, unsafe_allow_html=True)

                        st.session_state.train_msgs.append({
                            "role": "assistant",
                            "content": final_answer
                        })
                        st.session_state.processing_new_query = False

                        st.session_state.current_q = None

                    except Exception as e:
                        st.error(f"🚨 오류: {e}")
                        st.session_state.processing_new_query = False
