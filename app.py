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
    page_title="검단탑병원 인증조사 AI 전문가",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 🎨 CSS
# ============================================================
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

html, body, .stApp {
    background: #F5F8FC !important;
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
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    max-width: 100% !important;
}

/* Streamlit 기본 아이콘 깨짐 방지 */
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
    box-shadow: 8px 0 24px rgba(15,45,80,0.03);
}

[data-testid="stSidebar"] > div {
    padding-top: 1.2rem !important;
}

.sidebar-box {
    background: linear-gradient(135deg, #F8FBFF 0%, #F0FFFC 100%);
    border: 1px solid #DCE7F3;
    border-radius: 18px;
    padding: 15px;
    margin-top: 12px;
    box-shadow: 0 4px 14px rgba(15,45,80,0.06);
}

.sidebar-title {
    font-size: 0.95rem;
    font-weight: 900;
    color: #002B5E;
    margin-bottom: 8px;
}

.sidebar-text {
    font-size: 0.82rem;
    color: #526174;
    line-height: 1.55;
}

/* 헤더 */
.enterprise-header {
    width: 100%;
    min-height: 76px;
    background:
        radial-gradient(circle at 10% 20%, rgba(17,175,166,0.22), transparent 25%),
        linear-gradient(135deg, #002B5E 0%, #004C86 48%, #0068A8 100%);
    border-radius: 0 0 22px 22px;
    padding: 14px 24px;
    margin: 0 0 14px 0;
    box-shadow: 0 12px 26px rgba(0,45,94,0.18);
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 18px;
    overflow: hidden;
    position: relative;
}

.enterprise-header::after {
    content: "";
    position: absolute;
    right: -90px;
    top: -120px;
    width: 280px;
    height: 280px;
    border-radius: 50%;
    background: rgba(255,255,255,0.09);
}

.enterprise-left {
    display: flex;
    align-items: center;
    gap: 14px;
    min-width: 0;
    position: relative;
    z-index: 2;
}

.enterprise-logo-box {
    width: 50px;
    height: 50px;
    border-radius: 16px;
    background: rgba(255,255,255,0.96);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 8px 18px rgba(0,0,0,0.12);
    overflow: hidden;
}

.enterprise-logo-box img {
    max-width: 42px !important;
    max-height: 42px !important;
    object-fit: contain !important;
}

.enterprise-title-wrap {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
}

.enterprise-eyebrow {
    color: rgba(255,255,255,0.78) !important;
    font-size: 0.78rem;
    font-weight: 700;
}

.enterprise-title {
    color: #FFFFFF !important;
    margin: 0;
    font-size: clamp(1.05rem, 2.1vw, 1.65rem) !important;
    font-weight: 900;
    letter-spacing: -1.2px;
    white-space: nowrap;
}

.enterprise-right {
    display: flex;
    align-items: center;
    gap: 12px;
    position: relative;
    z-index: 2;
}

.ai-badge,
.user-badge {
    color: #FFFFFF !important;
    border: 1px solid rgba(255,255,255,0.28);
    background: rgba(255,255,255,0.12);
    border-radius: 999px;
    padding: 8px 13px;
    font-size: 0.84rem;
    font-weight: 800;
}

/* 상단 탭 */
.mode-strip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #E8EEF5;
    border-radius: 999px;
    padding: 5px;
    margin: 0 0 10px 0;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.04);
}

.mode-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    border-radius: 999px;
    padding: 9px 15px;
    font-size: 0.92rem;
    font-weight: 900;
    color: #4B5E73 !important;
}

.mode-pill.active {
    background: #FFFFFF;
    color: #0068C9 !important;
    box-shadow: 0 5px 14px rgba(0,70,130,0.10);
    border: 1px solid rgba(0,104,201,0.18);
}

/* 히어로 */
.hero-card {
    background:
        radial-gradient(circle at 12% 30%, rgba(15,175,166,0.13), transparent 24%),
        linear-gradient(135deg, #FFFFFF 0%, #F1FBFF 56%, #F0FFFC 100%);
    border: 1px solid rgba(15,175,166,0.22);
    border-radius: 24px;
    box-shadow: 0 10px 30px rgba(15,45,80,0.08);
    padding: 26px 28px;
    min-height: 214px;
    display: flex;
    align-items: center;
    gap: 26px;
    position: relative;
    overflow: hidden;
}

.hero-card::after {
    content: "";
    position: absolute;
    right: -70px;
    bottom: -90px;
    width: 230px;
    height: 230px;
    border-radius: 50%;
    background: rgba(0,104,201,0.06);
}

.robot-box {
    width: 148px;
    height: 148px;
    border-radius: 36px;
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
    padding: 7px 11px;
    font-size: 0.82rem;
    font-weight: 900;
    margin-bottom: 12px;
}

.hero-title {
    font-size: clamp(1.35rem, 2.3vw, 2rem);
    line-height: 1.25;
    letter-spacing: -1.2px;
    margin: 0 0 10px 0;
    font-weight: 900;
    color: #0F1F35;
}

.hero-title b {
    color: #0FAFA6;
}

.hero-desc {
    color: #526174;
    font-size: 0.98rem;
    line-height: 1.7;
    margin-bottom: 17px;
    font-weight: 600;
}

.start-badge {
    display: inline-flex;
    align-items: center;
    gap: 9px;
    background: linear-gradient(135deg, #008B83 0%, #0FAFA6 100%);
    color: #FFFFFF;
    padding: 13px 20px;
    border-radius: 16px;
    font-weight: 900;
    box-shadow: 0 12px 22px rgba(15,175,166,0.22);
}

/* Streamlit 버튼을 카드처럼 */
div[data-testid="stButton"] > button {
    width: 100%;
    min-height: 92px;
    background: #FFFFFF !important;
    border: 1px solid #E0EAF5 !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 14px rgba(15,45,80,0.06) !important;
    color: #002B5E !important;
    font-weight: 900 !important;
    font-size: 0.96rem !important;
    text-align: left !important;
    padding: 18px 20px !important;
    transition: 0.15s ease-in-out !important;
}

div[data-testid="stButton"] > button:hover {
    border-color: #0FAFA6 !important;
    box-shadow: 0 8px 22px rgba(15,175,166,0.14) !important;
    transform: translateY(-1px);
}

.recommend-box {
    background: #FFFFFF;
    border: 1px solid #E0EAF5;
    border-radius: 18px;
    box-shadow: 0 4px 14px rgba(15,45,80,0.06);
    padding: 13px 16px;
    margin-top: 10px;
    margin-bottom: 14px;
    color: #2468B2;
    font-size: 0.88rem;
    font-weight: 800;
}

/* 오른쪽 예시 패널 */
.example-panel {
    background: rgba(255,255,255,0.92);
    border: 1px solid #DCE7F3;
    border-radius: 24px;
    box-shadow: 0 10px 30px rgba(15,45,80,0.08);
    padding: 19px;
}

.example-title {
    font-weight: 900;
    color: #0068C9;
    font-size: 1.08rem;
    margin-bottom: 14px;
}

.example-card {
    background: #FFFFFF;
    border: 1px solid #E2ECF6;
    border-radius: 18px;
    padding: 15px;
    margin-bottom: 12px;
    box-shadow: 0 3px 12px rgba(15,45,80,0.04);
}

.example-card-title {
    color: #0068C9;
    font-size: 0.94rem;
    font-weight: 900;
    margin-bottom: 8px;
}

.example-card-text {
    color: #405166;
    font-size: 0.84rem;
    line-height: 1.62;
    font-weight: 600;
}

.info-note {
    background: #EAF4FF;
    border: 1px solid rgba(0,104,201,0.12);
    border-radius: 14px;
    padding: 10px 12px;
    color: #31608F;
    font-size: 0.78rem;
    line-height: 1.55;
    font-weight: 700;
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
    .enterprise-right {
        display: none;
    }

    .hero-card {
        flex-direction: column;
        align-items: flex-start;
    }

    .example-panel {
        display: none;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 🔐 로그인
# ============================================================
if not st.session_state.get("authenticated", False):
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.05, 1])
    with col2:
        st.markdown("""
        <div style="
            background:rgba(255,255,255,0.94);
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
                인증조사 AI 전문가 시스템
            </div>
            <div style="text-align:center;color:#526174;font-size:0.92rem;margin-bottom:22px;line-height:1.6;">
                검단탑병원 5주기 인증조사 대비<br>
                지침서 기반 AI 질의응답 시스템입니다.
            </div>
        """, unsafe_allow_html=True)

        pwd = st.text_input("보안 코드 입력", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")

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
# 📌 세션
# ============================================================
if "search_msgs" not in st.session_state:
    st.session_state.search_msgs = []

if "queued_query" not in st.session_state:
    st.session_state.queued_query = None

SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다. 출처 표시 없이 정답만 짧게 대답하십시오."""

# ============================================================
# 📌 사이드바
# ============================================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"):
        st.image("검단탑병원-로고_고화질.png")

    st.markdown("""
    <div class="sidebar-box">
        <div class="sidebar-title">📡 실시간 상태</div>
        <div class="sidebar-text">● 인증 지침서 데이터 동기화 완료</div>
        <div class="sidebar-text">● 검색 엔진 정상 가동</div>
        <div class="sidebar-text">● AI 질의응답 모드</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 인증조사 AI 메뉴")

    if st.button("💬 AI 질문하기", use_container_width=True):
        st.session_state.queued_query = "인증조사 준비를 위해 가장 먼저 확인해야 할 핵심 항목을 알려줘"
        st.rerun()

    if st.button("🔎 지침서 검색", use_container_width=True):
        st.session_state.queued_query = "5주기 인증지침서에서 실무자가 반드시 확인해야 할 핵심 내용을 요약해줘"
        st.rerun()

    if st.button("❓ 예상질문", use_container_width=True):
        st.session_state.queued_query = "조사위원이 현장에서 물어볼 수 있는 예상질문을 알려줘"
        st.rerun()

    if st.button("✅ 체크리스트", use_container_width=True):
        st.session_state.queued_query = "인증조사 대비 부서별 체크리스트를 만들어줘"
        st.rerun()

    if st.button("📁 준비자료", use_container_width=True):
        st.session_state.queued_query = "인증조사 시 준비해야 할 확인자료 목록을 알려줘"
        st.rerun()

# ============================================================
# 로고 Base64
# ============================================================
logo_html = ""
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}'>"

# ============================================================
# 상단 헤더
# ============================================================
st.markdown(f"""
<div class="enterprise-header">
    <div class="enterprise-left">
        <div class="enterprise-logo-box">{logo_html}</div>
        <div class="enterprise-title-wrap">
            <div class="enterprise-eyebrow">GEOMDAN TOP HOSPITAL · ACCREDITATION AI</div>
            <h1 class="enterprise-title">검단탑병원 인증조사 AI 전문가</h1>
        </div>
    </div>
    <div class="enterprise-right">
        <div class="ai-badge">AI 전문가</div>
        <div class="user-badge">인증담당자님</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="mode-strip">
    <div class="mode-pill active">🔍 인증 지침서 검색</div>
    <div class="mode-pill">💬 AI 질의응답</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 질문 실행 함수
# ============================================================
def run_query(query):
    st.session_state.search_msgs.append({"role": "user", "content": query})

    with st.chat_message("user", avatar="👤"):
        st.markdown(query)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("💭 지침서를 분석하며 생각중..."):
            try:
                docs = vdb.similarity_search(query, k=12)
                ctx_str = "\n\n".join([d.page_content for d in docs])
                full_ans = st.write_stream(
                    get_intelligent_response(
                        f"{SYS_RULE}\n\n[원문 데이터]\n{ctx_str}\n\n질문: {query}"
                    )
                )
                st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
            except Exception as e:
                st.error(f"🚨 오류: {e}")

# ============================================================
# 초기 화면
# ============================================================
if len(st.session_state.search_msgs) == 0:
    left, right = st.columns([4.2, 1.4], gap="large")

    with left:
        st.markdown("""
        <div class="hero-card">
            <div class="robot-box">
                <div class="robot-face"></div>
            </div>
            <div class="hero-content">
                <div class="hero-kicker">🏅 5주기 인증조사 대비 AI 도우미</div>
                <div class="hero-title">안녕하세요. 인증조사 <b>AI 전문가</b>입니다.</div>
                <div class="hero-desc">
                    인증지침서 검색, 조사위원 예상질문, 준비자료 확인, 부서별 체크포인트를
                    지침서 기반으로 빠르게 확인할 수 있습니다.
                </div>
                <div class="start-badge">💬 아래 입력창에서 채팅 시작하기 ›</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("❓ 조사위원 예상질문\n\n특정 항목에 대해 물어볼 가능성이 높은 질문 확인", use_container_width=True):
                st.session_state.queued_query = "조사위원이 현장에서 물어볼 수 있는 예상질문을 항목별로 정리해줘"
                st.rerun()

        with c2:
            if st.button("✅ 부서별 체크리스트\n\n간호부, 감염관리, QI, 총무 등 준비사항 확인", use_container_width=True):
                st.session_state.queued_query = "인증조사 대비 부서별 체크리스트를 만들어줘"
                st.rerun()

        with c3:
            if st.button("📁 준비자료 확인\n\n조사 시 제시 가능한 문서와 점검표 확인", use_container_width=True):
                st.session_state.queued_query = "인증조사 시 준비해야 할 확인자료 목록을 알려줘"
                st.rerun()

        c4, c5, c6 = st.columns(3)
        with c4:
            if st.button("🧾 답변 요약\n\n긴 지침 내용을 실무 답변으로 요약", use_container_width=True):
                st.session_state.queued_query = "인증지침서 내용을 실무자가 답변하기 쉽게 요약하는 방법으로 정리해줘"
                st.rerun()

        with c5:
            if st.button("⚖️ 근거 중심 답변\n\n지침서 기반 대응 방향 정리", use_container_width=True):
                st.session_state.queued_query = "인증조사 답변 시 근거 중심으로 답변하는 예시를 알려줘"
                st.rerun()

        with c6:
            if st.button("🧠 실무형 질문 대응\n\n현장에서 답변하기 쉬운 문장 구성", use_container_width=True):
                st.session_state.queued_query = "현장 직원이 인증조사에서 답변하기 쉬운 실무형 답변 예시를 만들어줘"
                st.rerun()

        st.markdown("""
        <div class="recommend-box">
            ✨ 추천 질문&nbsp;&nbsp;
            낙상 발생 시 보고 절차는 어떻게 되나요?&nbsp;&nbsp;&nbsp;
            감염관리위원회의 역할은 무엇인가요?&nbsp;&nbsp;&nbsp;
            직원교육 이수 관리는 어떻게 준비하나요?
        </div>
        """, unsafe_allow_html=True)

        r1, r2, r3 = st.columns(3)
        with r1:
            if st.button("낙상 발생 시 보고 절차", use_container_width=True):
                st.session_state.queued_query = "낙상 발생 시 보고 절차는 어떻게 되나요?"
                st.rerun()
        with r2:
            if st.button("감염관리위원회 역할", use_container_width=True):
                st.session_state.queued_query = "감염관리위원회의 역할은 무엇인가요?"
                st.rerun()
        with r3:
            if st.button("직원교육 이수 관리", use_container_width=True):
                st.session_state.queued_query = "직원교육 이수 관리는 어떻게 준비하나요?"
                st.rerun()

    with right:
        st.markdown("""
        <div class="example-panel">
            <div class="example-title">✨ AI 답변 구조 예시</div>

            <div class="example-card">
                <div class="example-card-title">답변 요약</div>
                <div class="example-card-text">
                    낙상예방을 위해 고위험 환자 평가, 환경관리, 교육, 모니터링 등
                    다각적인 중재를 시행하고 낙상 발생 시 재발방지 활동을 강화합니다.
                </div>
            </div>

            <div class="example-card">
                <div class="example-card-title">근거</div>
                <div class="example-card-text">
                    • 환자안전 관련 지침<br>
                    • 낙상예방 관리 절차<br>
                    • 5주기 인증기준 관련 항목
                </div>
            </div>

            <div class="example-card">
                <div class="example-card-title">예상 확인자료</div>
                <div class="example-card-text">
                    • 낙상 고위험 환자 평가 기록지<br>
                    • 낙상 발생 보고서<br>
                    • 교육자료 및 교육일지<br>
                    • 병실 환경 점검 체크리스트
                </div>
            </div>

            <div class="info-note">
                ⓘ 위 내용은 화면 예시입니다. 실제 답변은 업로드된 인증 지침서 데이터에 기반하여 생성됩니다.
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 기존 채팅 출력
# ============================================================
for m in st.session_state.search_msgs:
    avatar = "👤" if m["role"] == "user" else "🤖"
    with st.chat_message(m["role"], avatar=avatar):
        st.markdown(m["content"])

# ============================================================
# 버튼으로 예약된 질문 실행
# ============================================================
if st.session_state.queued_query:
    pending_query = st.session_state.queued_query
    st.session_state.queued_query = None
    run_query(pending_query)

# ============================================================
# 하단 입력창
# ============================================================
if query := st.chat_input("질문하거나 답변하십시오..."):
    run_query(query)
