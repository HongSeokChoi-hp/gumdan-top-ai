import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
import random
import time
import base64

# ============================================================
# 🔑 [보안] Streamlit Secrets 및 API 키 연동 (원본 로직)
# ============================================================
try:
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
    initial_sidebar_state="auto"
)

# ============================================================
# 🎨 [최종 보정] PC 인터페이스 무조건 강제 + 빈공간 감소 + 모바일 검정바 버그 해결 CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
    
    /* PC 인터페이스와 동일한 회색 배경색 */
    .stApp { background-color: #f0f2f6 !important; }
    p, span, div, li, h1, h2, h3, h4 { color: #111827 !important; }
    
    /* 🚨 사이드바 완벽 영구 삭제 (화살표도 안 보임) */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton, footer { display: none !important; visibility: hidden !important; }
    
    /* 빈공간 극대 감소 */
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 1300px !important; 
    }

    /* 💎 마지막 사진 스타일 상단 네이비 배너 (천장 고정) */
    .dashboard-header { 
        background: linear-gradient(90deg, #003366 0%, #005691 100%) !important; 
        padding: 10px 20px; 
        border-radius: 8px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .dashboard-header img { height: 26px !important; flex-shrink: 0; background: white; padding: 2px; border-radius: 4px;} 
    .dashboard-header * { color: #ffffff !important; } 
    .dashboard-header h1 { margin: 0; font-size: clamp(0.9rem, 4vw, 1.25rem) !important; font-weight: 800; letter-spacing: -1px !important; flex-shrink: 0;}

    /* 마지막 사진 탭 스타일 라디오 버튼 (상단 배너 바로 아래 천장 고정) */
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        position: sticky !important;
        top: 0px !important; 
        z-index: 1000 !important;
        background-color: #f0f2f6 !important; 
        padding-top: 8px !important;
        padding-bottom: 8px !important;
        margin-top: 5px;
    }
    div[role="radiogroup"] {
        background-color: #e0e0e0; /* 탭 배경색 */
        padding: 4px;
        border-radius: 10px;
        display: inline-flex;
        gap: 0px;
        width: 100%;
        overflow: hidden;
    }
    /* 탭 스타일 라디오 */
    div[role="radiogroup"] label {
        margin: 0 !important;
        font-weight: 700 !important;
        font-size: clamp(0.7rem, 3vw, 0.9rem) !important;
        border-radius: 8px;
        padding: 6px 10px !important;
        flex-grow: 1;
        text-align: center;
        cursor: pointer;
    }
    /* 선택되지 않은 탭 */
    div[role="radiogroup"] label[data-baseweb="radio"] { background-color: transparent; }
    div[role="radiogroup"] label[data-baseweb="radio"] * { color: #555 !important; }
    /* 선택된 탭 */
    div[role="radiogroup"] label[data-baseweb="radio"] + div { background-color: transparent !important; border: none !important; width:0;height:0;overflow:hidden;}
    div[role="radiogroup"] label[data-baseweb="radio"]:has(input[checked]) { background-color: #ffffff !important; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    div[role="radiogroup"] label[data-baseweb="radio"]:has(input[checked]) * { color: #003366 !important; }

    /* 🚨 모바일 가시성 해결의 핵심: PC 레이아웃(columns)을 모바일에서도 강제 유지 */
    .stColumns {
        display: flex !important;
        flex-direction: row !important; /* 모바일에서도 쌓지 않음! */
        flex-wrap: nowrap !important;
        gap: 10px !important;
        width: 100% !important;
    }
    /* 각 컬럼 너비 강제 고정 */
    [data-testid="column"] { 
        padding: 0 !important;
        overflow: visible !important;
    }
    
    /* 📱 모바일 화면에서는 오른쪽 답변 가이드 텍스트를 극도로 줄여서 쑤셔넣음 */
    @media (max-width: 768px) {
        .block-container { padding: 0.5rem 0.2rem !important; }
        .stColumns { gap: 4px !important; }
        
        .welcome-section img { height: 35px !important; }
        .welcome-section h2 { font-size: 0.8rem !important; }
        .welcome-section p { font-size: 0.6rem !important; }
        
        /* 오른쪽 답변 가이드 극도로 축소 */
        .answer-structure { padding: 5px !important; }
        .answer-structure h3 { font-size: 0.65rem !important; margin-bottom: 5px !important;}
        .answer-structure li { padding: 4px !important; margin-bottom: 4px !important;}
        .answer-structure-title { font-size: 0.6rem !important; }
        .answer-structure-content { font-size: 0.55rem !important; }
        .answer-structure-icon { font-size: 0.7rem !important; margin-right: 2px !important; }
    }

    /* 환영 섹션 */
    .welcome-section {
        background-color: white !important;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
        border: 1px solid #e2e8f0;
    }
    .welcome-section img { height: 50px !important; flex-shrink: 0; }
    .welcome-section h2 { color: #111827 !important; margin: 0 0 5px 0; font-size: clamp(0.9rem, 3.5vw, 1.25rem);}
    .welcome-section p { color: #6b7280 !important; margin: 0; font-size: clamp(0.7rem, 2.5vw, 0.9rem); line-height: 1.4;}

    /* 💎 마지막 사진 스타일 Colored 아이콘 답변 양식 (말풍선 내) */
    .answer-card { background: #ffffff; border-radius: 8px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);}
    .answer-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 8px; }
    .answer-card-header img { height: 30px; }
    .answer-card-header h3 { margin: 0; font-size: 1.1rem; color: #111827; }
    
    .answer-section { margin-bottom: 12px; }
    .answer-section-title { font-weight: 700; display: flex; align-items: center; gap: 5px; margin-bottom: 5px; font-size: 0.95rem;}
    .answer-section-content { color: #475569; font-size: 0.9rem; line-height: 1.6; }
    
    /* 요약 (Blue) */
    .answer-summary { color: #005691; }
    .answer-summary-content { background: #f1f5f9; padding: 10px; border-radius: 6px; }
    /* 근거 (Navy) */
    .answer-grounds { color: #003366; }
    /* 자료 (Yellow/Gold) */
    .answer-data { color: #ca8a04; }

    /* 채팅 말풍선 */
    [data-testid="stChatMessage"] { 
        background-color: transparent !important; 
        padding: 0 !important; 
        margin-bottom: 10px;
    }
    /* 유저 말풍선 (마지막 사진 스타일 blue bubble) */
    [data-testid="stChatMessage"]:has(.st-emotion-cache-zt5igj) .stMarkdown {
        background-color: #dbeafe; 
        padding: 8px 12px; 
        border-radius: 12px 12px 0 12px; 
        max-width: 80%; 
        margin-left: auto;
    }
    /* AI 말풍선 (card style) */
    [data-testid="stChatMessage"]:has(.st-emotion-cache-p4m0av) {
        /* AI 아바타 제거 */
    }
    [data-testid="stChatMessage"]:has(.st-emotion-cache-p4m0av) > div:first-child { display: none; }
    [data-testid="stChatMessage"]:has(.st-emotion-cache-p4m0av) .stMarkdown {
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 12px; 
        box-shadow: 0 1px 4px rgba(0,0,0,0.05); 
        margin-right: auto;
        border: 1px solid #e2e8f0;
    }

    /* 🚨 모바일 검정색 입력창 해결 + PC 스타일 전송바 */
    div[data-testid="stChatInput"] { 
        position: sticky !important; 
        bottom: 0 !important; 
        padding: 8px 0 !important; 
        background: #ffffff !important; /* 모바일 오류의 원인 그라데이션 제거, 단색 배경 강제 */
        z-index: 1001 !important; 
        margin-top: 10px;
    }
    div[data-testid="stChatInput"] > div { 
        background-color: #3e506d !important; /* 딥 네이비 입력창 배경 */
        border: none !important;
        border-radius: 20px !important; 
        margin: 0 10px !important;
    }
    div[data-testid="stChatInput"] textarea {
        color: #ffffff !important; 
        -webkit-text-fill-color: #ffffff !important; 
        background-color: transparent !important;
        padding: 10px 15px !important;
        font-size: 0.9rem !important;
    }
    ::placeholder { color: rgba(255, 255, 255, 0.7) !important; opacity: 1; } /* 플레이스홀더 흰색 */
    
    div[data-testid="stChatInput"] button {
        background-color: transparent !important; 
        border: none !important;
    }
    div[data-testid="stChatInput"] svg {
        fill: white !important; /* 전송 아이콘 흰색 */
    }
    
    /* 훈련 모드 파란색 ghost button */
    .stButton > button {
        background-color: #ffffff !important;
        color: #005691 !important;
        border: 1px solid #005691 !important;
        font-weight: 700 !important;
        font-size: clamp(0.7rem, 2.5vw, 0.9rem) !important;
    }
    .stButton > button:hover { background-color: #e6f7ff !important;}
</style>
""", unsafe_allow_html=True)

# 🔐 [인증] 로그인 로직
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; font-weight:800; margin-bottom:20px;'>인증조사 AI 도우미 시스템</h3>", unsafe_allow_html=True)
        pwd = st.text_input("보안 코드 입력", type="password", placeholder="코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: 
            st.session_state.authenticated = True
            st.rerun()
        elif pwd: 
            st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# 🧠 [엔진] DB 로드
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

logo_html = ""
avatar_base64 = ""
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        avatar_base64 = f"data:image/png;base64,{encoded_string}"
        logo_html = f"<img src='data:image/png;base64,{encoded_string}'>"

# 상단 배너
st.markdown(f"""
<div class='dashboard-header'>
    {logo_html}
    <h1>검단탑병원 인증조사 AI 전문가</h1>
</div>
""", unsafe_allow_html=True)

if "current_mode" not in st.session_state: st.session_state.current_mode = "🔍 인증 지침서 검색"

# 탭 스타일 라디오 (빈공간 감소 위해 sticky)
st.session_state.current_mode = st.radio("모드 선택", ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"], horizontal=True, label_visibility="collapsed")
mode = st.session_state.current_mode

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# 메인 콘텐츠 레이아웃 (모바일에서도 가로 레이아웃 강제 유지!)
main_col, answer_col = st.columns([2.2, 1])

# 🚨 [중요] 마지막 사진 스타일의 Colored 답변 양식 프롬프트
SYS_RULE = f"""당신은 '검단탑병원 인증조사 AI 전문가'입니다. 
제공된 [원문 데이터]를 분석하여 조사위원의 질문에 대해 아래의 Colored 답변 양식(HTML)으로만 출력하십시오. 출처 표시는 하지 마십시오.

양식 예시:
<div class='answer-card'>
    <div class='answer-card-header'>
        <img src='{avatar_base64}'>
        <h3>AI 전문가 답변</h3>
    </div>
    <div class='answer-section answer-summary'>
        <div class='answer-section-title'>💡 답변 요약</div>
        <div class='answer-section-content answer-summary-content'>(핵심 요약)</div>
    </div>
    <div class='answer-section answer-grounds'>
        <div class='answer-section-title'>⚖️ 근거</div>
        <div class='answer-section-content'>(지침서 항목 및 정확한 페이지 번호)</div>
    </div>
    <div class='answer-section answer-data'>
        <div class='answer-section-title'>📂 예상 확인자료</div>
        <div class='answer-section-content'>(기록지, 보고서 등)</div>
    </div>
</div>
"""

with main_col:
    if "current_welcome_shown" not in st.session_state: st.session_state.current_welcome_shown = None
    
    if st.session_state.current_welcome_shown != mode:
        st.markdown(f"""
        <div class='welcome-section'>
            {logo_html}
            <div>
                <h2>안녕하세요! 인증조사 AI 전문가입니다</h2>
                <p>인증지침 검색, 예상질문 대비, 체크리스트 확인까지 AI와 함께 더 쉽고 빠르게!</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.current_welcome_shown = mode

    # 🔍 모드 1: 지침서 검색
    if mode == "🔍 인증 지침서 검색":
        for m in st.session_state.search_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

    # 🕵️‍♂️ 모드 2: 모의훈련
    elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":
        st.info("💡 감독관의 질문에 답변하고 지침서 기반 채점을 받아보세요.")
        if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
            with st.chat_message("assistant"):
                with st.spinner("💭 감독관이 질문을 생성하고 있습니다..."):
                    random_docs = vdb.similarity_search(random.choice(["지침", "규정"]), k=3)
                    sample_ctx = "\n\n".join([f"[메타데이터: {d.metadata}]\n{d.page_content}" for d in random_docs])
                    q_stream = get_intelligent_response(f"인증평가 감독관 질문 1개 생성. 행동 말고 규정 지식을 묻는 날카로운 질문을 하세요.\n내용:\n{sample_ctx}")
                    st.session_state.current_q = st.write_stream(q_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
        for m in st.session_state.train_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"], unsafe_allow_html=True)

with answer_col:
    # 오른쪽 답변 구조 예시 섹션
    st.markdown(f"""
    <div class='answer-structure'>
        <h3>🌟 AI 표준 답변 가이드</h3>
        <ul>
            <li>
                <div class='answer-structure-title'><span class='answer-structure-icon'>💡요약</span>답변 요약</div>
                <div class='answer-structure-content'>낙상예방을 위해 고위험 환자 평가, 환경관리, 교육 등을 시행하며 재발 방지 활동을 강화합니다.</div>
            </li>
            <li>
                <div class='answer-structure-title'><span class='answer-structure-icon'>⚖️근거</span>근거</div>
                <div class='answer-structure-content'>• 환자안전 지침서 3.4 낙상예방관리 (p.12)<br>• 5주기 인증기준 IPR.2.1 (p.45)</div>
            </li>
            <li>
                <div class='answer-structure-title'><span class='answer-structure-icon'>📂자료</span>예상 확인자료</div>
                <div class='answer-structure-content'>• 낙상 고위험 환자 평가 기록지<br>• 낙상 발생 보고서 및 RCA 분석<br>• 병동 환경 점검 체크리스트</div>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 🚨 하단 입력창 답변 프로세스 (모바일 검정바 버그 해결 디자인)
if query := st.chat_input("질문하거나 답변하십시오..."):
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        with st.chat_message("assistant"):
            with st.spinner("💭 지침서를 분석 중..."):
                try:
                    docs = vdb.similarity_search(query, k=12)
                    ctx_str = "\n\n".join([f"[메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
                    full_ans = st.write_stream(get_intelligent_response(f"{SYS_RULE}\n\n[원문 데이터]\n{ctx_str}\n\n질문: {query}"))
                    st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
                except Exception as e: st.error(f"🚨 오류: {e}")
    else:
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)
            with st.chat_message("assistant"):
                with st.spinner("💭 답변 채점 중..."):
                    try:
                        docs = vdb.similarity_search(st.session_state.current_q, k=8)
                        ctx_str = "\n\n".join([f"[메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
                        # 🚨 채점 모드에서도 Colored 양식 적용
                        full_ans = st.write_stream(get_intelligent_response(f"감독관 시선 채점 및 보완. 아래 Colored 양식(HTML)으로 출력하십시오. 출처 금지.\n질문: {st.session_state.current_q}\n답변: {query}\n데이터:\n{ctx_str}"))
                        st.session_state.train_msgs.append({"role": "assistant", "content": full_ans})
                        st.session_state.current_q = None
                    except Exception as e: st.error(f"🚨 오류: {e}")
