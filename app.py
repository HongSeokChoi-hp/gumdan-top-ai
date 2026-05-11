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
    # 여러 개의 API 키 중 랜덤 선택하여 부하 분산
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다. 설정 확인이 필요합니다.")
    st.stop()

# 시스템 보안 코드 (기획자 설정)
SET_PASSWORD = "0366"

# 페이지 전체 설정
st.set_page_config(
    page_title="검단탑병원 인증조사 AI 전문가",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 🎨 [디자인] CSS 스타일링
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    :root {
        --gt-navy: #003B73;
        --gt-navy-dark: #002B5E;
        --gt-blue: #0068C9;
        --gt-blue-2: #0B7FEA;
        --gt-mint: #0FAFA6;
        --gt-mint-dark: #008B83;
        --gt-bg: #F5F8FC;
        --gt-card: #FFFFFF;
        --gt-border: #DCE7F3;
        --gt-text: #111827;
        --gt-sub: #526174;
        --gt-soft-blue: #EEF7FF;
        --gt-soft-mint: #E9FBF8;
        --gt-shadow: 0 10px 30px rgba(15, 45, 80, 0.08);
        --gt-shadow-soft: 0 4px 14px rgba(15, 45, 80, 0.06);
    }

    * {
        font-family: 'Pretendard', sans-serif !important;
        box-sizing: border-box;
    }

    html, body, .stApp {
        background: linear-gradient(180deg, #F7FAFD 0%, #F3F7FB 100%) !important;
    }

    p, span, div, li, h1, h2, h3, h4, h5, h6 {
        color: var(--gt-text) !important;
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

    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.75rem !important;
    }

    /* ============================================================
       로그인 화면
    ============================================================ */
    .login-card {
        background: rgba(255,255,255,0.94);
        border: 1px solid var(--gt-border);
        border-radius: 26px;
        padding: 34px 30px 30px 30px;
        box-shadow: var(--gt-shadow);
        backdrop-filter: blur(14px);
    }

    .login-title {
        text-align: center;
        color: var(--gt-navy-dark) !important;
        font-weight: 900;
        margin-top: 8px;
        margin-bottom: 8px;
        letter-spacing: -0.7px;
        font-size: 1.35rem;
    }

    .login-subtitle {
        text-align: center;
        color: var(--gt-sub) !important;
        font-size: 0.92rem;
        margin-bottom: 22px;
        line-height: 1.6;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 14px !important;
        border: 1.5px solid #C9D9EA !important;
        background: #FFFFFF !important;
        padding: 13px 14px !important;
        color: var(--gt-text) !important;
        box-shadow: 0 3px 10px rgba(0, 50, 100, 0.04) !important;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: var(--gt-blue) !important;
        box-shadow: 0 0 0 4px rgba(0,104,201,0.12) !important;
    }

    /* ============================================================
       상단 헤더
    ============================================================ */
    .enterprise-header {
        width: 100%;
        min-height: 76px;
        background:
            radial-gradient(circle at 10% 20%, rgba(17, 175, 166, 0.22), transparent 25%),
            linear-gradient(135deg, #002B5E 0%, #004C86 48%, #0068A8 100%);
        border-radius: 0 0 22px 22px;
        padding: 14px 24px;
        margin: 0 0 14px 0;
        box-shadow: 0 12px 26px rgba(0, 45, 94, 0.18);
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
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.12);
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
        letter-spacing: -0.2px;
    }

    .enterprise-title {
        color: #FFFFFF !important;
        margin: 0;
        font-size: clamp(1.05rem, 2.1vw, 1.65rem) !important;
        font-weight: 900;
        letter-spacing: -1.2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .enterprise-right {
        display: flex;
        align-items: center;
        gap: 12px;
        position: relative;
        z-index: 2;
        flex-shrink: 0;
    }

    .ai-badge {
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.35);
        background: rgba(255,255,255,0.13);
        border-radius: 999px;
        padding: 8px 13px;
        font-size: 0.84rem;
        font-weight: 800;
        backdrop-filter: blur(10px);
    }

    .user-badge {
        color: #FFFFFF !important;
        border: 1px solid rgba(255,255,255,0.25);
        background: rgba(255,255,255,0.10);
        border-radius: 999px;
        padding: 8px 13px;
        font-size: 0.84rem;
        font-weight: 700;
        backdrop-filter: blur(10px);
    }

    div[data-testid="stVerticalBlock"] > div:has(.enterprise-header) {
        position: sticky !important;
        top: 0 !important;
        z-index: 1000 !important;
        background: transparent !important;
        padding-top: 0 !important;
    }

    /* ============================================================
       사이드바
    ============================================================ */
    [data-testid="stSidebar"] {
        background: #FFFFFF !important;
        border-right: 1px solid var(--gt-border) !important;
        box-shadow: 8px 0 24px rgba(15, 45, 80, 0.03);
    }

    [data-testid="stSidebar"] > div {
        padding-top: 1.1rem !important;
    }

    .side-panel {
        padding: 8px 4px 12px 4px;
    }

    .side-title {
        font-weight: 900;
        color: var(--gt-navy-dark) !important;
        font-size: 0.96rem;
        margin: 12px 0 12px 0;
        letter-spacing: -0.5px;
    }

    .side-menu-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 11px 12px;
        margin-bottom: 7px;
        border-radius: 15px;
        color: #4E5F73 !important;
        font-weight: 800;
        font-size: 0.92rem;
        background: transparent;
        border: 1px solid transparent;
    }

    .side-menu-item.active {
        background: linear-gradient(135deg, #E8FAF7 0%, #EEF7FF 100%);
        color: var(--gt-mint) !important;
        border: 1px solid rgba(15,175,166,0.18);
        box-shadow: 0 5px 12px rgba(15,175,166,0.07);
    }

    .side-menu-icon {
        width: 28px;
        height: 28px;
        border-radius: 10px;
        background: #F1F6FB;
        display: flex;
        align-items: center;
        justify-content: center;
        color: inherit !important;
        flex-shrink: 0;
    }

    .status-card {
        background: linear-gradient(135deg, #F8FBFF 0%, #F0FFFC 100%);
        border: 1px solid var(--gt-border);
        border-radius: 18px;
        padding: 15px;
        margin-top: 14px;
        box-shadow: var(--gt-shadow-soft);
    }

    .status-title {
        font-weight: 900;
        color: var(--gt-navy-dark) !important;
        font-size: 0.92rem;
        margin-bottom: 8px;
    }

    .status-line {
        font-size: 0.82rem;
        color: var(--gt-sub) !important;
        line-height: 1.55;
        margin: 4px 0;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #12B981;
        margin-right: 6px;
        box-shadow: 0 0 0 4px rgba(18,185,129,0.12);
    }

    /* ============================================================
       상단 안내 탭
    ============================================================ */
    .mode-strip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #E8EEF5;
        border-radius: 999px;
        padding: 5px;
        margin: 0 0 2px 0;
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
        color: var(--gt-blue) !important;
        box-shadow: 0 5px 14px rgba(0, 70, 130, 0.10);
        border: 1px solid rgba(0,104,201,0.18);
    }

    /* ============================================================
       홈/채팅 히어로
    ============================================================ */
    .home-shell {
        display: grid;
        grid-template-columns: minmax(0, 1fr) 360px;
        gap: 18px;
        margin-top: 2px;
        margin-bottom: 12px;
    }

    .hero-card {
        background:
            radial-gradient(circle at 12% 30%, rgba(15,175,166,0.13), transparent 24%),
            linear-gradient(135deg, #FFFFFF 0%, #F1FBFF 56%, #F0FFFC 100%);
        border: 1px solid rgba(15, 175, 166, 0.22);
        border-radius: 24px;
        box-shadow: var(--gt-shadow);
        padding: 26px 28px;
        min-height: 214px;
        display: flex;
        align-items: center;
        gap: 26px;
        position: relative;
        overflow: hidden;
    }

    .hero-card::before {
        content: "+";
        position: absolute;
        left: 28px;
        top: 32px;
        color: rgba(15,175,166,0.12) !important;
        font-size: 42px;
        font-weight: 900;
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
        box-shadow: 0 16px 30px rgba(0, 104, 201, 0.12);
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
        box-shadow: inset 0 -8px 18px rgba(255,255,255,0.05);
    }

    .robot-face::before {
        content: "◠  ◠";
        position: absolute;
        color: #31E6DF !important;
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
        color: white !important;
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
        min-width: 0;
        position: relative;
        z-index: 2;
    }

    .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        color: var(--gt-blue) !important;
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
        color: #0F1F35 !important;
    }

    .hero-title b {
        color: var(--gt-mint) !important;
    }

    .hero-desc {
        color: var(--gt-sub) !important;
        font-size: 0.98rem;
        line-height: 1.7;
        margin-bottom: 17px;
        font-weight: 600;
    }

    .hero-actions {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }

    .start-chat-btn {
        display: inline-flex;
        align-items: center;
        gap: 9px;
        background: linear-gradient(135deg, #008B83 0%, #0FAFA6 100%);
        color: #FFFFFF !important;
        padding: 13px 20px;
        border-radius: 16px;
        font-weight: 900;
        box-shadow: 0 12px 22px rgba(15,175,166,0.22);
        border: 1px solid rgba(255,255,255,0.26);
    }

    .quick-chip {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        color: #00776F !important;
        background: rgba(255,255,255,0.82);
        border: 1px solid rgba(15,175,166,0.20);
        padding: 10px 14px;
        border-radius: 999px;
        font-size: 0.88rem;
        font-weight: 800;
        box-shadow: 0 6px 14px rgba(15, 45, 80, 0.05);
    }

    .right-panel {
        background: rgba(255,255,255,0.92);
        border: 1px solid var(--gt-border);
        border-radius: 24px;
        box-shadow: var(--gt-shadow);
        padding: 19px;
    }

    .panel-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 900;
        color: var(--gt-blue) !important;
        font-size: 1.08rem;
        letter-spacing: -0.5px;
        margin-bottom: 14px;
    }

    .answer-mini-card {
        background: #FFFFFF;
        border: 1px solid #E2ECF6;
        border-radius: 18px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 3px 12px rgba(15,45,80,0.04);
    }

    .answer-mini-title {
        color: var(--gt-blue) !important;
        font-size: 0.94rem;
        font-weight: 900;
        margin-bottom: 8px;
    }

    .answer-mini-text {
        color: #405166 !important;
        font-size: 0.84rem;
        line-height: 1.62;
        font-weight: 600;
    }

    .answer-mini-text ul {
        padding-left: 18px;
        margin: 0;
    }

    .answer-mini-text li {
        color: #405166 !important;
        margin-bottom: 4px;
    }

    .info-note {
        background: #EAF4FF;
        border: 1px solid rgba(0,104,201,0.12);
        border-radius: 14px;
        padding: 10px 12px;
        color: #31608F !important;
        font-size: 0.78rem;
        line-height: 1.55;
        font-weight: 700;
    }

    /* ============================================================
       기능 카드
    ============================================================ */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 12px;
    }

    .feature-card {
        background: #FFFFFF;
        border: 1px solid #E0EAF5;
        border-radius: 20px;
        padding: 18px;
        box-shadow: var(--gt-shadow-soft);
        min-height: 106px;
        display: flex;
        align-items: center;
        gap: 14px;
        position: relative;
        overflow: hidden;
    }

    .feature-card::after {
        content: "›";
        position: absolute;
        right: 17px;
        top: 50%;
        transform: translateY(-50%);
        color: #8AA0B7 !important;
        font-size: 30px;
        font-weight: 400;
    }

    .feature-icon {
        width: 52px;
        height: 52px;
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.55rem;
        flex-shrink: 0;
        background: #EEF7FF;
    }

    .feature-icon.mint {
        background: #E9FBF8;
    }

    .feature-title {
        color: var(--gt-navy-dark) !important;
        font-size: 1rem;
        font-weight: 900;
        letter-spacing: -0.4px;
        margin-bottom: 6px;
    }

    .feature-desc {
        color: var(--gt-sub) !important;
        font-size: 0.84rem;
        line-height: 1.5;
        font-weight: 600;
        padding-right: 18px;
    }

    .recommend-strip {
        background: #FFFFFF;
        border: 1px solid #E0EAF5;
        border-radius: 18px;
        box-shadow: var(--gt-shadow-soft);
        padding: 13px 16px;
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;
        overflow-x: auto;
        white-space: nowrap;
    }

    .recommend-title {
        color: var(--gt-blue) !important;
        font-weight: 900;
        font-size: 0.92rem;
        flex-shrink: 0;
    }

    .recommend-q {
        color: #2468B2 !important;
        font-size: 0.86rem;
        font-weight: 800;
        flex-shrink: 0;
    }

    /* ============================================================
       채팅 입력창
    ============================================================ */
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
        box-shadow: 0 12px 26px rgba(0, 104, 201, 0.11) !important;
    }

    div[data-testid="stChatInput"] textarea {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        background-color: #FFFFFF !important;
        padding: 14px 16px !important;
        font-weight: 600 !important;
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: #8A9AAF !important;
    }

    div[data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #005691 0%, #0B7FEA 100%) !important;
        color: white !important;
        border-radius: 50% !important;
        padding: 5px !important;
        margin-right: 10px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        visibility: visible !important;
        opacity: 1 !important;
        box-shadow: 0 6px 16px rgba(0,104,201,0.24) !important;
    }

    div[data-testid="stChatInput"] svg {
        fill: white !important;
        width: 20px !important;
        height: 20px !important;
    }

    /* ============================================================
       채팅 메시지
    ============================================================ */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border-radius: 18px !important;
        padding: 16px 20px !important;
        box-shadow: var(--gt-shadow-soft) !important;
        margin-bottom: 12px !important;
        border: 1px solid #E0EAF5 !important;
    }

    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        line-height: 1.72 !important;
        font-size: 0.98rem !important;
    }

    .stAlert {
        border-radius: 16px !important;
    }

    div[data-testid="stSpinner"] {
        color: var(--gt-blue) !important;
        font-weight: 800 !important;
    }

    /* 모바일 대응 */
    @media (max-width: 1100px) {
        .home-shell {
            grid-template-columns: 1fr;
        }

        .right-panel {
            display: none;
        }

        .feature-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 720px) {
        .enterprise-header {
            min-height: 68px;
            padding: 12px 14px;
            border-radius: 0 0 18px 18px;
        }

        .enterprise-logo-box {
            width: 42px;
            height: 42px;
            border-radius: 14px;
        }

        .enterprise-right {
            display: none;
        }

        .hero-card {
            flex-direction: column;
            align-items: flex-start;
            padding: 22px;
        }

        .robot-box {
            width: 96px;
            height: 96px;
            border-radius: 26px;
        }

        .robot-face {
            width: 66px;
            height: 50px;
            border-radius: 20px;
        }

        .robot-face::before {
            font-size: 20px;
            left: 15px;
            top: 10px;
            letter-spacing: 5px;
        }

        .robot-face::after {
            width: 28px;
            height: 28px;
            left: 19px;
            bottom: -36px;
        }

        .feature-grid {
            grid-template-columns: 1fr;
        }

        .quick-chip {
            width: 100%;
            justify-content: center;
        }

        .start-chat-btn {
            width: 100%;
            justify-content: center;
        }
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 🔐 [인증] 로그인 로직
# ============================================================
if not st.session_state.get("authenticated", False):
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.05, 1])
    with col2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        if os.path.exists("검단탑병원-로고_고화질.png"):
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("""
            <div class='login-title'>인증조사 AI 전문가 시스템</div>
            <div class='login-subtitle'>
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
# 🧠 [엔진] DB 로드
# ============================================================
@st.cache_resource
def load_intelligent_db():
    if not os.path.exists("faiss_index_saved"):
        return None, "faiss_index_saved 데이터가 없습니다."
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=random.choice(API_KEYS))
        vdb = FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
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
# 🗂️ [메인 UI]
# ============================================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"):
        st.image("검단탑병원-로고_고화질.png")

    st.markdown("""
    <div class='side-panel'>
        <div class='side-title'>인증조사 AI 메뉴</div>

        <div class='side-menu-item active'>
            <div class='side-menu-icon'>💬</div>
            <div>AI 질문하기</div>
        </div>

        <div class='side-menu-item'>
            <div class='side-menu-icon'>🔎</div>
            <div>지침서 검색</div>
        </div>

        <div class='side-menu-item'>
            <div class='side-menu-icon'>❓</div>
            <div>예상질문</div>
        </div>

        <div class='side-menu-item'>
            <div class='side-menu-icon'>✅</div>
            <div>체크리스트</div>
        </div>

        <div class='side-menu-item'>
            <div class='side-menu-icon'>📁</div>
            <div>준비자료</div>
        </div>

        <div class='side-menu-item'>
            <div class='side-menu-icon'>⭐</div>
            <div>즐겨찾기</div>
        </div>

        <div class='status-card'>
            <div class='status-title'>📡 실시간 상태</div>
            <div class='status-line'><span class='status-dot'></span>인증 지침서 데이터 동기화 완료</div>
            <div class='status-line'>검색 엔진 정상 가동</div>
            <div class='status-line'>v2.7.0 디자인 개선 적용</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

logo_html = ""
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}'>"

st.markdown(f"""
<div class='enterprise-header'>
    <div class='enterprise-left'>
        <div class='enterprise-logo-box'>
            {logo_html}
        </div>
        <div class='enterprise-title-wrap'>
            <div class='enterprise-eyebrow'>GEOMDAN TOP HOSPITAL · ACCREDITATION AI</div>
            <h1 class='enterprise-title'>검단탑병원 인증조사 AI 전문가</h1>
        </div>
    </div>
    <div class='enterprise-right'>
        <div class='ai-badge'>AI 전문가</div>
        <div class='user-badge'>인증담당자님</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='mode-strip'>
    <div class='mode-pill active'>🔍 인증 지침서 검색</div>
    <div class='mode-pill'>💬 AI 질의응답</div>
</div>
""", unsafe_allow_html=True)

if "search_msgs" not in st.session_state:
    st.session_state.search_msgs = []

SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다. 출처 표시 없이 정답만 짧게 대답하십시오."""

# ============================================================
# 🧭 초기 안내 화면
# ============================================================
if len(st.session_state.search_msgs) == 0:
    st.markdown("""
    <div class='home-shell'>
        <div>
            <div class='hero-card'>
                <div class='robot-box'>
                    <div class='robot-face'></div>
                </div>
                <div class='hero-content'>
                    <div class='hero-kicker'>🏅 5주기 인증조사 대비 AI 도우미</div>
                    <div class='hero-title'>안녕하세요. 인증조사 <b>AI 전문가</b>입니다.</div>
                    <div class='hero-desc'>
                        인증지침서 검색, 조사위원 예상질문, 준비자료 확인, 부서별 체크포인트를
                        지침서 기반으로 빠르게 확인할 수 있습니다.
                    </div>
                    <div class='hero-actions'>
                        <div class='start-chat-btn'>💬 아래 입력창에서 채팅 시작하기 ›</div>
                        <div class='quick-chip'>💡 낙상예방 질문</div>
                        <div class='quick-chip'>💡 감염관리 질문</div>
                        <div class='quick-chip'>💡 환자확인 질문</div>
                    </div>
                </div>
            </div>

            <div style='height:14px;'></div>

            <div class='feature-grid'>
                <div class='feature-card'>
                    <div class='feature-icon'>❓</div>
                    <div>
                        <div class='feature-title'>조사위원 예상질문</div>
                        <div class='feature-desc'>특정 항목에 대해 조사위원이 물어볼 가능성이 높은 질문을 확인</div>
                    </div>
                </div>

                <div class='feature-card'>
                    <div class='feature-icon mint'>✅</div>
                    <div>
                        <div class='feature-title'>부서별 체크리스트</div>
                        <div class='feature-desc'>간호부, 감염관리, QI, 총무 등 부서별 준비사항 확인</div>
                    </div>
                </div>

                <div class='feature-card'>
                    <div class='feature-icon mint'>📁</div>
                    <div>
                        <div class='feature-title'>준비자료 확인</div>
                        <div class='feature-desc'>조사 시 제시 가능한 문서, 교육자료, 점검표 목록 확인</div>
                    </div>
                </div>

                <div class='feature-card'>
                    <div class='feature-icon'>🧾</div>
                    <div>
                        <div class='feature-title'>답변 요약</div>
                        <div class='feature-desc'>긴 지침 내용을 실무자가 바로 말할 수 있는 답변으로 요약</div>
                    </div>
                </div>

                <div class='feature-card'>
                    <div class='feature-icon'>⚖️</div>
                    <div>
                        <div class='feature-title'>근거 중심 답변</div>
                        <div class='feature-desc'>지침서 데이터 기반으로 인증조사 대응 방향 정리</div>
                    </div>
                </div>

                <div class='feature-card'>
                    <div class='feature-icon mint'>🧠</div>
                    <div>
                        <div class='feature-title'>실무형 질문 대응</div>
                        <div class='feature-desc'>현장에서 답변하기 쉬운 형태로 핵심 문장 구성</div>
                    </div>
                </div>
            </div>

            <div class='recommend-strip'>
                <div class='recommend-title'>✨ 추천 질문</div>
                <div class='recommend-q'>낙상 발생 시 보고 절차는 어떻게 되나요?</div>
                <div class='recommend-q'>감염관리위원회의 역할은 무엇인가요?</div>
                <div class='recommend-q'>직원교육 이수 관리는 어떻게 준비하나요?</div>
            </div>
        </div>

        <div class='right-panel'>
            <div class='panel-title'>✨ AI 답변 구조 예시</div>

            <div class='answer-mini-card'>
                <div class='answer-mini-title'>답변 요약</div>
                <div class='answer-mini-text'>
                    낙상예방을 위해 고위험 환자 평가, 환경관리, 교육, 모니터링 등 다각적인 중재를 시행하고,
                    낙상 발생 시 보고 및 분석을 통해 재발방지 활동을 강화합니다.
                </div>
            </div>

            <div class='answer-mini-card'>
                <div class='answer-mini-title'>근거</div>
                <div class='answer-mini-text'>
                    <ul>
                        <li>환자안전 관련 지침</li>
                        <li>낙상예방 관리 절차</li>
                        <li>5주기 인증기준 관련 항목</li>
                    </ul>
                </div>
            </div>

            <div class='answer-mini-card'>
                <div class='answer-mini-title'>예상 확인자료</div>
                <div class='answer-mini-text'>
                    <ul>
                        <li>낙상 고위험 환자 평가 기록지</li>
                        <li>낙상 발생 보고서</li>
                        <li>교육자료 및 교육일지</li>
                        <li>병실 환경 점검 체크리스트</li>
                    </ul>
                </div>
            </div>

            <div class='info-note'>
                ⓘ 위 내용은 화면 예시입니다. 실제 답변은 업로드된 인증 지침서 데이터에 기반하여 생성됩니다.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 🔍 지침서 검색 채팅 출력
# ============================================================
for m in st.session_state.search_msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ============================================================
# 🚨 하단 입력창 답변 프로세스
# ============================================================
if query := st.chat_input("질문하거나 답변하십시오..."):
    st.session_state.search_msgs.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
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
