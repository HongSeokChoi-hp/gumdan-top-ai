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
    layout="wide"
)

# ============================================================
# 🎨 PC / 모바일 완전 분리 CSS + 빈 공간 채우기 (추천 질문)
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
    
    .stApp { background-color: #f8f9fa !important; }
    p, span, div, li, h1, h2, h3, h4 { color: #111827 !important; }
    
    /* 방해 요소 영구 삭제 */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton, footer { display: none !important; visibility: hidden !important; }
    
    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 1200px !important; 
    }

    /* 공통 배너 */
    .dashboard-header { 
        background: linear-gradient(90deg, #003366 0%, #005691 100%) !important; 
        padding: 15px 25px; 
        border-radius: 8px; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 15px;
    }
    .dashboard-header img { height: 35px !important; flex-shrink: 0; background: white; padding: 4px; border-radius: 6px;} 
    .dashboard-header * { color: #ffffff !important; } 
    .dashboard-header h1 { margin: 0; font-size: 1.4rem !important; font-weight: 800; }

    /* 라디오 버튼 (모드 선택) */
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        background-color: #ffffff !important;
        padding: 8px 15px !important;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
    }
    div[role="radiogroup"] label { font-weight: 700 !important; color: #475569 !important; padding: 5px 10px !important;}
    div[role="radiogroup"] label[data-baseweb="radio"]:has(input[checked]) * { color: #003366 !important; }

    /* 환영 섹션 */
    .welcome-section {
        background-color: white !important;
        padding: 25px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 20px;
        margin-bottom: 25px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .welcome-section img { height: 60px !important; flex-shrink: 0; }
    .welcome-section h2 { color: #111827 !important; margin: 0 0 10px 0; font-size: 1.4rem; font-weight: 800; }
    .welcome-section p { color: #475569 !important; margin: 0; font-size: 1rem; line-height: 1.5; }

    /* 💎 휑한 공간을 예쁘게 채워줄 추천 질문 섹션 */
    .quick-prompts {
        background-color: transparent;
        padding: 10px 0 20px 0;
        margin-bottom: 10px;
    }
    .quick-prompts h4 { margin: 0 0 15px 0; font-size: 1.1rem; color: #334155 !important; font-weight: 800;}
    .prompt-chips { display: flex; gap: 12px; flex-wrap: wrap; }
    .prompt-chips span {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 10px 18px;
        border-radius: 25px;
        font-size: 0.95rem;
        color: #005691 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        font-weight: 600;
    }

    /* 우측 AI 가이드 구조 */
    .answer-structure {
        background-color: white !important;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .answer-structure h3 { color: #003366 !important; margin: 0 0 15px 0; font-size: 1.1rem; font-weight: 800; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; }
    .answer-structure ul { list-style: none; padding: 0; margin: 0; }
    .answer-structure li { margin-bottom: 15px; background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #005691; }
    .answer-structure-title { font-weight: 700; color: #005691 !important; margin-bottom: 6px; font-size: 1rem;}
    .answer-structure-content { color: #475569 !important; font-size: 0.9rem; line-height: 1.5; }

    /* =================================================== */
    /* 📱 모바일 전용 UI */
    /* =================================================== */
    @media (max-width: 768px) {
        div[data-testid="column"]:nth-of-type(2) { display: none !important; }
        .block-container { padding-top: 0.5rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        .dashboard-header { padding: 10px; margin-bottom: 10px; }
        .dashboard-header img { height: 28px !important; }
        .dashboard-header h1 { font-size: 1.1rem !important; }
        .welcome-section { padding: 15px; margin-bottom: 15px; flex-direction: column; text-align: center; gap: 10px; }
        .welcome-section img { height: 45px !important; }
        .welcome-section h2 { font-size: 1.2rem !important; margin-bottom: 4px; }
        .welcome-section p { font-size: 0.9rem !important; }
        div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) { padding: 5px !important; margin-bottom: 10px; }
        
        /* 모바일에서는 추천 칩 크기 조절 */
        .prompt-chips span { padding: 8px 14px; font-size: 0.85rem; }
    }
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
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}'>"

# 상단 배너
st.markdown(f"""
<div class='dashboard-header'>
    {logo_html}
    <h1>검단탑병원 인증조사 AI 전문가</h1>
</div>
""", unsafe_allow_html=True)

# 모드 선택
if "current_mode" not in st.session_state: st.session_state.current_mode = "🔍 인증 지침서 검색"
st.session_state.current_mode = st.radio("모드 선택", ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"], horizontal=True, label_visibility="collapsed")
mode = st.session_state.current_mode

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# PC: 2분할 레이아웃 / 모바일: 우측 가이드 자동 숨김 처리
main_col, answer_col = st.columns([2.2, 1])

SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다. 
사용자의 질문에 대해 반드시 제공된 [원문 데이터]를 분석하여 아래의 3단 구조 양식에 맞춰 답변하십시오.

### 💡 답변 요약
(질문에 대한 핵심 내용을 2~3줄로 명확하게 요약)

### ⚖️ 근거
(답변의 근거가 되는 지침서 항목, 절차서 번호 및 **정확한 페이지 번호**를 불릿 기호(•)를 사용하여 나열. 예: • 환자안전 지침서 3.4 (p.12))

### 📂 예상 확인자료
(현장 평가 시 확인하거나 준비해야 할 관련 기록지, 보고서, 체크리스트 등을 불릿 기호(•)를 사용하여 나열)
"""

with main_col:
    # 환영 섹션
    st.markdown(f"""
    <div class='welcome-section'>
        {logo_html}
        <div>
            <h2>안녕하세요! 인증조사 AI 전문가입니다</h2>
            <p>방대한 인증 지침서를 단 몇 초 만에 검색하고, AI 감독관과 함께 훈련하세요.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 💎 텅 빈 공간을 채워줄 추천 질문 섹션 추가
    st.markdown("""
    <div class='quick-prompts'>
        <h4>💡 자주 묻는 핵심 질문</h4>
        <div class='prompt-chips'>
            <span>💬 낙상 발생 시 보고 절차는 어떻게 되나요?</span>
            <span>💬 감염관리 위원회의 주요 역할은?</span>
            <span>💬 병동 환경 점검 체크리스트 항목 알려줘</span>
            <span>💬 심폐소생술(CPR) 교육 이수 기준은?</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if mode == "🔍 인증 지침서 검색":
        for m in st.session_state.search_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":
        st.info("💡 하단의 채팅창에 답변을 입력하면 AI가 지침서 기반으로 채점합니다.")
        if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
            with st.chat_message("assistant"):
                with st.spinner("💭 질문 생성 중..."):
                    random_docs = vdb.similarity_search(random.choice(["지침", "규정"]), k=3)
                    sample_ctx = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in random_docs])
                    q_stream = get_intelligent_response(f"인증평가 감독관 질문 1개 생성. 행동 말고 규정 지식을 묻는 날카로운 질문을 하세요.\n내용:\n{sample_ctx}")
                    st.session_state.current_q = st.write_stream(q_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
        for m in st.session_state.train_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

with answer_col:
    st.markdown(f"""
    <div class='answer-structure'>
        <h3>🌟 AI 표준 답변 가이드</h3>
        <ul>
            <li>
                <div class='answer-structure-title'>💡 답변 요약</div>
                <div class='answer-structure-content'>낙상예방을 위해 고위험 환자 평가, 환경관리, 교육 등을 시행하며 재발 방지 활동을 강화합니다.</div>
            </li>
            <li>
                <div class='answer-structure-title'>⚖️ 근거</div>
                <div class='answer-structure-content'>• 환자안전 지침서 3.4 낙상예방관리 (p.12)<br>• 5주기 인증기준 IPR.2.1 (p.45)</div>
            </li>
            <li>
                <div class='answer-structure-title'>📂 예상 확인자료</div>
                <div class='answer-structure-content'>• 낙상 고위험 환자 평가 기록지<br>• 낙상 발생 보고서 및 RCA 분석<br>• 병동 환경 점검 체크리스트</div>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 하단 채팅창 (순정 폼 유지 - 에러 방지)
if query := st.chat_input("질문하거나 답변하십시오..."):
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        with st.chat_message("assistant"):
            with st.spinner("💭 지침서 분석 중..."):
                try:
                    docs = vdb.similarity_search(query, k=12)
                    ctx_str = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
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
                        ctx_str = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
                        full_ans = st.write_stream(get_intelligent_response(f"감독관 시선 채점 및 보완. 출처 금지.\n질문: {st.session_state.current_q}\n답변: {query}\n데이터:\n{ctx_str}"))
                        st.session_state.train_msgs.append({"role": "assistant", "content": full_ans})
                        st.session_state.current_q = None
                    except Exception as e: st.error(f"🚨 오류: {e}")
