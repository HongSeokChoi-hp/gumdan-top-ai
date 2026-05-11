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

st.set_page_config(
    page_title="검단탑병원 인증조사 AI 도우미",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 🎨 디자인 CSS
# ============================================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, .stApp {
    background: #F4F7FB !important;
    font-family: 'Pretendard', sans-serif !important;
}

body, p, span, div, li, h1, h2, h3, h4, h5, h6, button, input, textarea {
    font-family: 'Pretendard', sans-serif !important;
}

[data-testid="stHeader"] {
    display: none !important;
}

#creatorBadge,
.viewerBadge_container__1QSob,
.stDeployButton,
footer {
    display: none !important;
    visibility: hidden !important;
}

.block-container {
    padding-top: 0.8rem !important;
    padding-bottom: 0rem !important;
    max-width: 1480px !important;
}

/* Streamlit 아이콘 깨짐 방지 */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessageAvatarIcon"],
[data-testid="stChatMessageAvatarIcon"] * {
    font-family: "Material Symbols Rounded", "Material Symbols Outlined", sans-serif !important;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #DCE7F3 !important;
    box-shadow: 8px 0 24px rgba(15,45,80,0.04);
}

[data-testid="stSidebar"] > div {
    padding-top: 1.2rem !important;
}

.sidebar-status {
    background: linear-gradient(135deg, #F8FBFF 0%, #F0FFFC 100%);
    border: 1px solid #DCE7F3;
    border-radius: 18px;
    padding: 15px;
    margin: 12px 0 18px 0;
    box-shadow: 0 4px 14px rgba(15,45,80,0.06);
}

.sidebar-status-title {
    font-size: 0.95rem;
    font-weight: 900;
    color: #002B5E;
    margin-bottom: 8px;
}

.sidebar-status-line {
    font-size: 0.82rem;
    color: #526174;
    line-height: 1.65;
}

/* 상단 헤더 */
.top-header {
    width: 100%;
    min-height: 92px;
    background:
        radial-gradient(circle at 74% 28%, rgba(48, 157, 255, 0.18), transparent 22%),
        linear-gradient(135deg, #002B5E 0%, #003F7A 48%, #0068A8 100%);
    border-radius: 18px;
    padding: 18px 28px;
    margin-bottom: 18px;
    box-shadow: 0 14px 34px rgba(0,45,94,0.18);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    overflow: hidden;
    position: relative;
}

.top-header::after {
    content: "";
    position: absolute;
    right: -90px;
    top: -120px;
    width: 290px;
    height: 290px;
    border-radius: 50%;
    background: rgba(255,255,255,0.08);
}

.header-left {
    display: flex;
    align-items: center;
    gap: 16px;
    min-width: 0;
    position: relative;
    z-index: 2;
}

.header-logo {
    height: 48px;
    min-width: 120px;
    border-radius: 10px;
    background: #FFFFFF;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 5px 8px;
    box-shadow: 0 8px 18px rgba(0,0,0,0.12);
}

.header-logo img {
    max-height: 40px !important;
    max-width: 160px !important;
    object-fit: contain !important;
}

.header-title-wrap {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.header-title {
    color: #FFFFFF !important;
    margin: 0;
    font-size: clamp(1.25rem, 2vw, 1.9rem) !important;
    font-weight: 900;
    letter-spacing: -1.3px;
}

.header-subtitle {
    color: rgba(255,255,255,0.82) !important;
    font-size: 0.92rem;
    font-weight: 700;
}

.header-right {
    display: flex;
    gap: 10px;
    position: relative;
    z-index: 2;
}

.header-badge {
    color: #FFFFFF !important;
    border: 1px solid rgba(255,255,255,0.28);
    background: rgba(255,255,255,0.13);
    border-radius: 999px;
    padding: 9px 15px;
    font-size: 0.86rem;
    font-weight: 900;
}

/* 현재 페이지 표시 */
.page-chip-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
}

.page-chip {
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    padding: 9px 15px;
    font-size: 0.92rem;
    font-weight: 900;
    background: #FFFFFF;
    color: #0068C9 !important;
    border: 1px solid rgba(0,104,201,0.18);
    box-shadow: 0 5px 14px rgba(0,70,130,0.08);
}

/* 히어로 */
.hero-card {
    background:
        radial-gradient(circle at 12% 28%, rgba(15,175,166,0.13), transparent 24%),
        linear-gradient(135deg, #FFFFFF 0%, #F1FBFF 55%, #F0FFFC 100%);
    border: 1px solid rgba(15,175,166,0.22);
    border-radius: 24px;
    box-shadow: 0 10px 30px rgba(15,45,80,0.08);
    padding: 30px;
    min-height: 230px;
    display: flex;
    align-items: center;
    gap: 28px;
    position: relative;
    overflow: hidden;
}

.hero-card::after {
    content: "";
    position: absolute;
    right: -72px;
    bottom: -98px;
    width: 250px;
    height: 250px;
    border-radius: 50%;
    background: rgba(0,104,201,0.06);
}

.robot-box {
    width: 150px;
    height: 150px;
    border-radius: 38px;
    background: linear-gradient(180deg, #FFFFFF 0%, #EAF8FF 100%);
    border: 1px solid rgba(0,104,201,0.12);
    box-shadow: 0 16px 30px rgba(0,104,201,0.12);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    position: relative;
    z-index: 2;
}

.robot-face {
    width: 92px;
    height: 70px;
    border-radius: 28px;
    background: linear-gradient(135deg, #063A5B 0%, #082E4C 100%);
    position: relative;
}

.robot-face::before {
    content: "◠  ◠";
    position: absolute;
    color: #31E6DF;
    font-size: 28px;
    font-weight: 900;
    left: 22px;
    top: 14px;
    letter-spacing: 7px;
}

.robot-face::after {
    content: "✚";
    position: absolute;
    width: 34px;
    height: 34px;
    border-radius: 12px;
    background: linear-gradient(135deg, #0FAFA6 0%, #16C7B7 100%);
    color: white;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    left: 29px;
    bottom: -48px;
    box-shadow: 0 8px 16px rgba(15,175,166,0.22);
}

.hero-content {
    flex: 1;
    position: relative;
    z-index: 2;
}

.hero-kicker {
    display: inline-flex;
    color: #0068C9;
    background: #EAF4FF;
    border: 1px solid rgba(0,104,201,0.16);
    border-radius: 999px;
    padding: 7px 12px;
    font-size: 0.83rem;
    font-weight: 900;
    margin-bottom: 12px;
}

.hero-title {
    font-size: clamp(1.55rem, 2.4vw, 2.15rem);
    line-height: 1.25;
    letter-spacing: -1.4px;
    margin: 0 0 11px 0;
    font-weight: 900;
    color: #0F1F35;
}

.hero-title b {
    color: #0FAFA6;
}

.hero-desc {
    color: #526174;
    font-size: 1rem;
    line-height: 1.75;
    margin-bottom: 17px;
    font-weight: 600;
}

.hero-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.hero-tag {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    color: #00776F;
    background: rgba(255,255,255,0.82);
    border: 1px solid rgba(15,175,166,0.20);
    padding: 10px 14px;
    border-radius: 999px;
    font-size: 0.88rem;
    font-weight: 900;
    box-shadow: 0 6px 14px rgba(15,45,80,0.05);
}

/* 가이드 패널 */
.guide-panel {
    background: rgba(255,255,255,0.96);
    border: 1px solid #DCE7F3;
    border-radius: 24px;
    box-shadow: 0 10px 30px rgba(15,45,80,0.08);
    padding: 20px;
}

.guide-title {
    font-weight: 900;
    color: #002B5E;
    font-size: 1.12rem;
    margin-bottom: 14px;
}

.guide-card {
    background: #FFFFFF;
    border: 1px solid #E2ECF6;
    border-radius: 18px;
    padding: 15px;
    margin-bottom: 12px;
    box-shadow: 0 3px 12px rgba(15,45,80,0.04);
}

.guide-card-title {
    color: #0068C9;
    font-size: 0.94rem;
    font-weight: 900;
    margin-bottom: 8px;
}

.guide-card-text {
    color: #405166;
    font-size: 0.84rem;
    line-height: 1.65;
    font-weight: 600;
}

/* 설명 박스 */
.info-box {
    background: #FFFFFF;
    border: 1px solid #E0EAF5;
    border-radius: 20px;
    box-shadow: 0 4px 14px rgba(15,45,80,0.06);
    padding: 20px;
    margin-bottom: 14px;
}

.info-box h3 {
    color: #002B5E !important;
    margin: 0 0 8px 0;
    font-size: 1.1rem;
    font-weight: 900;
}

.info-box p {
    color: #526174 !important;
    line-height: 1.7;
    font-size: 0.95rem;
    font-weight: 600;
}

/* 버튼 공통 */
div[data-testid="stButton"] > button {
    width: 100%;
    min-height: 66px;
    background: #FFFFFF !important;
    border: 1px solid #E0EAF5 !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 14px rgba(15,45,80,0.06) !important;
    color: #002B5E !important;
    font-weight: 900 !important;
    font-size: 0.94rem !important;
    text-align: left !important;
    padding: 15px 17px !important;
    transition: 0.15s ease-in-out !important;
}

div[data-testid="stButton"] > button:hover {
    border-color: #0FAFA6 !important;
    box-shadow: 0 8px 22px rgba(15,175,166,0.14) !important;
    transform: translateY(-1px);
}

/* 채팅 입력창 */
div[data-testid="stChatInput"] {
    position: sticky !important;
    bottom: 0 !important;
    padding: 10px 0 25px 0 !important;
    background: linear-gradient(180deg, rgba(245,248,252,0) 0%, rgba(245,248,252,0.96) 35%, rgba(245,248,252,1) 100%) !important;
    z-index: 1001 !important;
}

div[data-testid="stChatInput"] > div {
    background-color: #FFFFFF !important;
    border: 1.8px solid #0B7FEA !important;
    border-radius: 18px !important;
    margin: 0 6px !important;
    overflow: hidden !important;
    box-shadow: 0 12px 26px rgba(0,104,201,0.11) !important;
}

div[data-testid="stChatInput"] textarea {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    background-color: #FFFFFF !important;
    padding: 14px 16px !important;
    font-weight: 600 !important;
}

div[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #005691 0%, #0B7FEA 100%) !important;
    color: white !important;
    border-radius: 50% !important;
    margin-right: 10px !important;
    box-shadow: 0 6px 16px rgba(0,104,201,0.24) !important;
}

div[data-testid="stChatInput"] svg {
    fill: white !important;
}

/* 채팅 메시지 */
[data-testid="stChatMessage"] {
    background-color: #FFFFFF !important;
    border-radius: 18px !important;
    padding: 16px 20px !important;
    box-shadow: 0 4px 14px rgba(15,45,80,0.06) !important;
    margin-bottom: 12px !important;
    border: 1px solid #E0EAF5 !important;
}

[data-testid="stChatMessage"] p,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    line-height: 1.72 !important;
    font-size: 0.98rem !important;
}

.stAlert {
    border-radius: 16px !important;
}

@media (max-width: 1100px) {
    .header-right {
        display: none;
    }

    .hero-card {
        flex-direction: column;
        align-items: flex-start;
    }

    .guide-panel {
        display: none;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 🔐 로그인 로직
# ============================================================
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.15, 1])
    with col2:
        st.markdown("""
        <div style="
            background:rgba(255,255,255,0.96);
            border:1px solid #DCE7F3;
            border-radius:26px;
            padding:34px 30px 30px 30px;
            box-shadow:0 10px 30px rgba(15,45,80,0.08);
        ">
        """, unsafe_allow_html=True)

        if os.path.exists("검단탑병원-로고_고화질.png"):
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)

        st.markdown("""
            <div style="text-align:center;color:#002B5E;font-weight:900;font-size:1.35rem;margin-top:8px;margin-bottom:8px;">
                인증조사 AI 도우미 시스템
            </div>
            <div style="text-align:center;color:#526174;font-size:0.92rem;margin-bottom:22px;line-height:1.6;">
                검단탑병원 5주기 인증조사 대비<br>
                지침서 기반 AI 질의응답 시스템입니다.
            </div>
        """, unsafe_allow_html=True)

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

        st.markdown("</div>", unsafe_allow_html=True)

    st.stop()

# ============================================================
# 🧠 DB 로드
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
# 📌 세션 상태
# ============================================================
if "page" not in st.session_state:
    st.session_state.page = "홈"

if "search_msgs" not in st.session_state:
    st.session_state.search_msgs = []

if "train_msgs" not in st.session_state:
    st.session_state.train_msgs = []

if "expected_msgs" not in st.session_state:
    st.session_state.expected_msgs = []

if "checklist_msgs" not in st.session_state:
    st.session_state.checklist_msgs = []

if "document_msgs" not in st.session_state:
    st.session_state.document_msgs = []

if "summary_msgs" not in st.session_state:
    st.session_state.summary_msgs = []

if "current_q" not in st.session_state:
    st.session_state.current_q = None

if "queued_query" not in st.session_state:
    st.session_state.queued_query = None

# ============================================================
# 📌 시스템 프롬프트
# ============================================================
SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다. 
사용자의 질문에 대해 반드시 제공된 [원문 데이터]를 분석하여 아래의 3단 구조 양식에 맞춰 답변하십시오.

### 💡 답변 요약
(질문에 대한 핵심 내용을 2~3줄로 명확하게 요약)

### ⚖️ 근거
(답변의 근거가 되는 지침서 항목, 절차서 번호, 또는 인증기준을 불릿 기호(•)를 사용하여 나열)

### 📂 예상 확인자료
(현장 평가 시 확인하거나 준비해야 할 관련 기록지, 보고서, 체크리스트 등을 불릿 기호(•)를 사용하여 나열)
"""

EXPECTED_RULE = SYS_RULE + """

추가 지시:
사용자의 질문과 관련하여 조사위원이 현장에서 물어볼 가능성이 높은 질문을 우선 정리하고,
각 질문에 대해 실무자가 답변할 때의 핵심 포인트를 함께 제시하십시오.
"""

CHECKLIST_RULE = SYS_RULE + """

추가 지시:
사용자의 질문과 관련하여 부서 또는 업무 단위에서 점검해야 할 체크리스트를 만들어 주십시오.
체크리스트는 □ 형태로 정리하고, 준비자료와 확인 포인트를 구분하십시오.
"""

DOCUMENT_RULE = SYS_RULE + """

추가 지시:
사용자의 질문과 관련하여 인증조사 시 제시하거나 준비해야 할 문서, 기록지, 보고서, 점검표, 교육자료를 중심으로 정리하십시오.
"""

SUMMARY_RULE = SYS_RULE + """

추가 지시:
사용자의 질문에 대해 현장 직원이 실제 조사위원에게 말하기 쉬운 짧은 답변 문장으로 정리하십시오.
"""

# ============================================================
# 📌 공통 함수
# ============================================================
def set_page(page_name):
    st.session_state.page = page_name
    st.rerun()

def get_logo_html():
    if os.path.exists("검단탑병원-로고_고화질.png"):
        with open("검단탑병원-로고_고화질.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return f"<img src='data:image/png;base64,{encoded_string}'>"
    return ""

def get_msg_key_by_page(page_name):
    if page_name == "예상질문":
        return "expected_msgs"
    if page_name == "체크리스트":
        return "checklist_msgs"
    if page_name == "준비자료":
        return "document_msgs"
    if page_name == "답변요약":
        return "summary_msgs"
    return "search_msgs"

def get_rule_by_page(page_name):
    if page_name == "예상질문":
        return EXPECTED_RULE
    if page_name == "체크리스트":
        return CHECKLIST_RULE
    if page_name == "준비자료":
        return DOCUMENT_RULE
    if page_name == "답변요약":
        return SUMMARY_RULE
    return SYS_RULE

def run_ai_query(query, page_name="AI 질문하기"):
    msg_key = get_msg_key_by_page(page_name)
    rule = get_rule_by_page(page_name)

    st.session_state[msg_key].append({"role": "user", "content": query})

    with st.chat_message("user", avatar="👤"):
        st.markdown(query)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("💭 지침서를 분석하며 답변을 정리중..."):
            try:
                docs = vdb.similarity_search(query, k=12)
                ctx_str = "\n\n".join([d.page_content for d in docs])
                full_ans = st.write_stream(
                    get_intelligent_response(
                        f"{rule}\n\n[원문 데이터]\n{ctx_str}\n\n질문: {query}"
                    )
                )
                st.session_state[msg_key].append({"role": "assistant", "content": full_ans})
            except Exception as e:
                st.error(f"🚨 오류: {e}")

def show_chat_history(page_name):
    msg_key = get_msg_key_by_page(page_name)
    for m in st.session_state[msg_key]:
        avatar = "👤" if m["role"] == "user" else "🤖"
        with st.chat_message(m["role"], avatar=avatar):
            st.markdown(m["content"])

# ============================================================
# 📌 사이드바
# ============================================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"):
        st.image("검단탑병원-로고_고화질.png")

    st.markdown("""
    <div class="sidebar-status">
        <div class="sidebar-status-title">📡 시스템 상태</div>
        <div class="sidebar-status-line">● 인증 지침서 데이터 동기화 완료</div>
        <div class="sidebar-status-line">● 검색 엔진 정상 가동</div>
        <div class="sidebar-status-line">● Gemini API 연동 활성</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 메인 메뉴")

    if st.button("🏠 홈", use_container_width=True):
        set_page("홈")

    if st.button("🔎 인증 지침서 검색", use_container_width=True):
        set_page("AI 질문하기")

    if st.button("🕵️‍♂️ 실전 모의감독관 훈련", use_container_width=True):
        set_page("모의감독관")

    if st.button("❓ 예상질문", use_container_width=True):
        set_page("예상질문")

    if st.button("✅ 부서별 체크리스트", use_container_width=True):
        set_page("체크리스트")

    if st.button("📁 준비자료", use_container_width=True):
        set_page("준비자료")

    if st.button("🧾 답변요약", use_container_width=True):
        set_page("답변요약")

# ============================================================
# 📌 상단 헤더
# ============================================================
logo_html = get_logo_html()

st.markdown(f"""
<div class="top-header">
    <div class="header-left">
        <div class="header-logo">{logo_html}</div>
        <div class="header-title-wrap">
            <h1 class="header-title">검단탑병원 인증조사 AI 도우미</h1>
            <div class="header-subtitle">5주기 인증조사 대비 AI 전문가 시스템</div>
        </div>
    </div>
    <div class="header-right">
        <div class="header-badge">🌟 AI 전문가</div>
        <div class="header-badge">👤 인증담당자님</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="page-chip-wrap">
    <div class="page-chip">현재 화면 · {st.session_state.page}</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 📌 홈 화면
# ============================================================
if st.session_state.page == "홈":
    main_col, guide_col = st.columns([3.2, 1.25], gap="large")

    with main_col:
        st.markdown("""
        <div class="hero-card">
            <div class="robot-box">
                <div class="robot-face"></div>
            </div>
            <div class="hero-content">
                <div class="hero-kicker">🏅 5주기 인증조사 대비 AI 도우미</div>
                <div class="hero-title">안녕하세요. 인증조사 <b>AI 도우미</b>입니다.</div>
                <div class="hero-desc">
                    인증지침서 검색, 조사위원 예상질문, 준비자료 확인, 부서별 체크리스트,
                    실전 모의감독관 훈련까지 한 화면에서 이동할 수 있습니다.
                </div>
                <div class="hero-tags">
                    <div class="hero-tag">💡 지침서 기반 답변</div>
                    <div class="hero-tag">⚖️ 근거 중심 정리</div>
                    <div class="hero-tag">📂 확인자료 안내</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔎 인증 지침서 검색\n\n궁금한 인증 기준과 절차를 지침서 기반으로 확인", use_container_width=True):
                set_page("AI 질문하기")
        with c2:
            if st.button("🕵️‍♂️ 실전 모의감독관 훈련\n\nAI가 질문하고 답변을 지침서 기준으로 채점", use_container_width=True):
                set_page("모의감독관")
        with c3:
            if st.button("❓ 예상질문\n\n조사위원이 물어볼 가능성이 높은 질문 확인", use_container_width=True):
                set_page("예상질문")

        c4, c5, c6 = st.columns(3)
        with c4:
            if st.button("✅ 부서별 체크리스트\n\n부서별 인증조사 준비사항 점검", use_container_width=True):
                set_page("체크리스트")
        with c5:
            if st.button("📁 준비자료 확인\n\n조사 시 제시할 자료와 기록지 목록 확인", use_container_width=True):
                set_page("준비자료")
        with c6:
            if st.button("🧾 답변요약\n\n현장 직원이 말하기 쉬운 답변으로 정리", use_container_width=True):
                set_page("답변요약")

        st.markdown("""
        <div class="info-box">
            <h3>추천 질문</h3>
            <p>
                낙상 발생 시 보고 절차는 어떻게 되나요? · 감염관리위원회의 역할은 무엇인가요? ·
                직원교육 이수 관리는 어떻게 준비하나요?
            </p>
        </div>
        """, unsafe_allow_html=True)

        r1, r2, r3 = st.columns(3)
        with r1:
            if st.button("낙상 발생 시 보고 절차", use_container_width=True):
                st.session_state.page = "AI 질문하기"
                st.session_state.queued_query = "낙상 발생 시 보고 절차는 어떻게 되나요?"
                st.rerun()
        with r2:
            if st.button("감염관리위원회 역할", use_container_width=True):
                st.session_state.page = "AI 질문하기"
                st.session_state.queued_query = "감염관리위원회의 역할은 무엇인가요?"
                st.rerun()
        with r3:
            if st.button("직원교육 이수 관리", use_container_width=True):
                st.session_state.page = "AI 질문하기"
                st.session_state.queued_query = "직원교육 이수 관리는 어떻게 준비하나요?"
                st.rerun()

    with guide_col:
        st.markdown("""
        <div class="guide-panel">
            <div class="guide-title">📘 AI 표준 답변 가이드</div>

            <div class="guide-card">
                <div class="guide-card-title">💡 답변 요약</div>
                <div class="guide-card-text">
                    질문에 대한 핵심 내용을 2~3줄로 정리합니다.
                </div>
            </div>

            <div class="guide-card">
                <div class="guide-card-title">⚖️ 근거</div>
                <div class="guide-card-text">
                    지침서 항목, 절차서, 인증기준 등 근거를 정리합니다.
                </div>
            </div>

            <div class="guide-card">
                <div class="guide-card-title">📂 예상 확인자료</div>
                <div class="guide-card-text">
                    현장 평가 시 준비할 기록지, 보고서, 체크리스트를 정리합니다.
                </div>
            </div>

            <div class="guide-card">
                <div class="guide-card-title">🧭 사용 방식</div>
                <div class="guide-card-text">
                    좌측 메뉴 또는 가운데 카드를 눌러 원하는 화면으로 이동하세요.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 📌 AI 질문하기 / 검색 화면
# ============================================================
elif st.session_state.page == "AI 질문하기":
    st.markdown("""
    <div class="info-box">
        <h3>🔎 인증 지침서 AI 검색</h3>
        <p>
            궁금한 인증 기준, 절차, 준비자료, 현장 대응방법을 입력하면
            업로드된 지침서 데이터를 기반으로 3단 구조 답변을 생성합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    show_chat_history("AI 질문하기")

# ============================================================
# 📌 모의감독관 훈련 화면
# ============================================================
elif st.session_state.page == "모의감독관":
    st.markdown("""
    <div class="info-box">
        <h3>🕵️‍♂️ 실전 모의감독관 훈련</h3>
        <p>
            감독관 질문을 생성한 뒤, 하단 채팅창에 답변하면
            AI가 지침서 기반으로 답변을 채점하고 보완점을 제시합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("💭 감독관이 질문을 생성하고 있습니다..."):
                random_docs = vdb.similarity_search(random.choice(["지침", "규정"]), k=3)
                sample_ctx = "\n".join([d.page_content for d in random_docs])
                q_stream = get_intelligent_response(
                    f"인증평가 감독관 질문 1개 생성. 행동 말고 규정 지식을 묻는 날카로운 질문을 하세요.\n내용:\n{sample_ctx}"
                )
                st.session_state.current_q = st.write_stream(q_stream)
                st.session_state.train_msgs.append({
                    "role": "assistant",
                    "content": st.session_state.current_q
                })

    for m in st.session_state.train_msgs:
        avatar = "👤" if m["role"] == "user" else "🤖"
        with st.chat_message(m["role"], avatar=avatar):
            st.markdown(m["content"])

# ============================================================
# 📌 예상질문 화면
# ============================================================
elif st.session_state.page == "예상질문":
    st.markdown("""
    <div class="info-box">
        <h3>❓ 조사위원 예상질문</h3>
        <p>
            특정 기준, 부서, 업무를 입력하면 조사위원이 물어볼 가능성이 높은 질문과
            답변 핵심 포인트를 정리합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("낙상예방 예상질문", use_container_width=True):
            st.session_state.queued_query = "낙상예방과 관련해 조사위원 예상질문을 만들어줘"
            st.rerun()
    with q2:
        if st.button("감염관리 예상질문", use_container_width=True):
            st.session_state.queued_query = "감염관리와 관련해 조사위원 예상질문을 만들어줘"
            st.rerun()
    with q3:
        if st.button("직원교육 예상질문", use_container_width=True):
            st.session_state.queued_query = "직원교육과 관련해 조사위원 예상질문을 만들어줘"
            st.rerun()

    show_chat_history("예상질문")

# ============================================================
# 📌 체크리스트 화면
# ============================================================
elif st.session_state.page == "체크리스트":
    st.markdown("""
    <div class="info-box">
        <h3>✅ 부서별 체크리스트</h3>
        <p>
            부서명이나 업무명을 입력하면 인증조사 전 확인해야 할 체크리스트를 생성합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("간호부 체크리스트", use_container_width=True):
            st.session_state.queued_query = "간호부 인증조사 대비 체크리스트를 만들어줘"
            st.rerun()
    with q2:
        if st.button("감염관리 체크리스트", use_container_width=True):
            st.session_state.queued_query = "감염관리 인증조사 대비 체크리스트를 만들어줘"
            st.rerun()
    with q3:
        if st.button("총무부 체크리스트", use_container_width=True):
            st.session_state.queued_query = "총무부 인증조사 대비 체크리스트를 만들어줘"
            st.rerun()

    show_chat_history("체크리스트")

# ============================================================
# 📌 준비자료 화면
# ============================================================
elif st.session_state.page == "준비자료":
    st.markdown("""
    <div class="info-box">
        <h3>📁 준비자료 확인</h3>
        <p>
            인증조사 시 제시할 수 있는 기록지, 보고서, 점검표, 교육자료를 정리합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("낙상 관련 준비자료", use_container_width=True):
            st.session_state.queued_query = "낙상예방 관련 인증조사 준비자료 목록을 알려줘"
            st.rerun()
    with q2:
        if st.button("감염관리 준비자료", use_container_width=True):
            st.session_state.queued_query = "감염관리 관련 인증조사 준비자료 목록을 알려줘"
            st.rerun()
    with q3:
        if st.button("직원교육 준비자료", use_container_width=True):
            st.session_state.queued_query = "직원교육 관련 인증조사 준비자료 목록을 알려줘"
            st.rerun()

    show_chat_history("준비자료")

# ============================================================
# 📌 답변요약 화면
# ============================================================
elif st.session_state.page == "답변요약":
    st.markdown("""
    <div class="info-box">
        <h3>🧾 실무형 답변요약</h3>
        <p>
            지침서 내용을 현장 직원이 조사위원에게 말하기 쉬운 답변 문장으로 정리합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("환자확인 답변요약", use_container_width=True):
            st.session_state.queued_query = "환자확인 절차를 직원이 말하기 쉬운 답변으로 요약해줘"
            st.rerun()
    with q2:
        if st.button("낙상예방 답변요약", use_container_width=True):
            st.session_state.queued_query = "낙상예방 활동을 직원이 말하기 쉬운 답변으로 요약해줘"
            st.rerun()
    with q3:
        if st.button("감염관리 답변요약", use_container_width=True):
            st.session_state.queued_query = "감염관리 활동을 직원이 말하기 쉬운 답변으로 요약해줘"
            st.rerun()

    show_chat_history("답변요약")

# ============================================================
# 📌 예약 질문 실행
# ============================================================
if st.session_state.queued_query:
    pending_query = st.session_state.queued_query
    st.session_state.queued_query = None
    run_ai_query(pending_query, st.session_state.page)

# ============================================================
# 📌 하단 채팅 입력 처리
# ============================================================
chat_placeholder = "인증 지침에 관해 질문하십시오..."

if st.session_state.page == "모의감독관":
    chat_placeholder = "감독관 질문에 답변하십시오..."
elif st.session_state.page == "예상질문":
    chat_placeholder = "예상질문을 만들 기준, 부서, 항목을 입력하십시오..."
elif st.session_state.page == "체크리스트":
    chat_placeholder = "체크리스트를 만들 부서나 항목을 입력하십시오..."
elif st.session_state.page == "준비자료":
    chat_placeholder = "준비자료를 확인할 기준, 부서, 항목을 입력하십시오..."
elif st.session_state.page == "답변요약":
    chat_placeholder = "답변요약이 필요한 항목을 입력하십시오..."

if query := st.chat_input(chat_placeholder):
    if st.session_state.page == "모의감독관":
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": query})

            with st.chat_message("user", avatar="👤"):
                st.markdown(query)

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("💭 답변을 기반으로 채점중..."):
                    try:
                        docs = vdb.similarity_search(st.session_state.current_q, k=8)
                        ctx_str = "\n\n".join([d.page_content for d in docs])
                        full_ans = st.write_stream(
                            get_intelligent_response(
                                f"감독관 시선 채점 및 보완. 출처 금지.\n질문: {st.session_state.current_q}\n답변: {query}\n데이터:\n{ctx_str}"
                            )
                        )
                        st.session_state.train_msgs.append({
                            "role": "assistant",
                            "content": full_ans
                        })
                        st.session_state.current_q = None
                    except Exception as e:
                        st.error(f"🚨 오류: {e}")
        else:
            st.warning("먼저 '새로운 감독관 질문 생성' 버튼을 눌러 질문을 생성하세요.")
    else:
        target_page = st.session_state.page
        if target_page == "홈":
            target_page = "AI 질문하기"
            st.session_state.page = "AI 질문하기"
        run_ai_query(query, target_page)
