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
SYSTEM_NAME = "검단탑병원 인증 AI 시스템" # 🚨 명칭 통합 변수

st.set_page_config(
    page_title=SYSTEM_NAME, 
    page_icon="🏅", 
    layout="wide"
)

# ============================================================
# 🎨 [디자인 최종본] 가로폭 1800px 대폭 확장 + 명칭 통일
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
    
    /* 🚨 가로폭 제한 대폭 확대 (1600px -> 1800px) 화면 시원하게 꽉 채움 */
    .block-container { 
        max-width: 1800px !important; 
        margin: 0 auto !important;
        padding-top: 2rem !important; 
        padding-bottom: 0rem !important; 
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }

    /* 상단 네이비 배너 */
    .dashboard-header { 
        background: linear-gradient(90deg, #003366 0%, #005691 100%) !important; 
        padding: 25px 35px; 
        border-radius: 12px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
        display: flex; align-items: center; gap: 20px; 
        margin-bottom: 25px; 
    }
    .dashboard-header img { height: 45px !important; flex-shrink: 0; background: white; padding: 5px; border-radius: 8px;} 
    .dashboard-header * { color: #ffffff !important; } 
    .dashboard-header h1 { margin: 0; font-size: 1.8rem !important; font-weight: 800; letter-spacing: -1px !important;}

    /* 모드 선택 라디오 버튼 */
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        background-color: #ffffff !important; padding: 12px 20px !important; border-radius: 10px;
        border: 1px solid #e2e8f0; margin-bottom: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    div[role="radiogroup"] label { font-weight: 700 !important; color: #475569 !important; padding: 8px 16px !important; font-size: 1.05rem !important; }
    div[role="radiogroup"] label[data-baseweb="radio"]:has(input[checked]) * { color: #003366 !important; }

    /* 환영 섹션 */
    .welcome-section {
        background-color: white !important; padding: 35px; border-radius: 12px; border: 1px solid #e2e8f0;
        display: flex; align-items: center; gap: 25px; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .welcome-section img { height: 75px !important; flex-shrink: 0; }
    .welcome-section h2 { color: #111827 !important; margin: 0 0 10px 0; font-size: 1.6rem !important; font-weight: 800; }
    .welcome-section p { color: #475569 !important; margin: 0; font-size: 1.05rem !important; line-height: 1.6; }

    /* 클릭 버튼 디자인 */
    .quick-prompts-title { margin: 0 0 15px 0; font-size: 1.2rem !important; color: #1e293b !important; font-weight: 800;}
    div[data-testid="stButton"] button {
        background-color: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 25px !important;
        color: #005691 !important; font-weight: 600 !important; padding: 12px 20px !important;
        display: flex !important; justify-content: flex-start !important; text-align: left !important;
        width: 100% !important; transition: all 0.2s ease-in-out; font-size: 0.95rem !important;
    }
    div[data-testid="stButton"] button:hover {
        border-color: #005691 !important; background-color: #f0f9ff !important;
        transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }

    /* 우측 AI 가이드 */
    .answer-structure {
        background-color: white !important; padding: 25px; border-radius: 12px; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .answer-structure h3 { color: #003366 !important; margin: 0 0 18px 0; font-size: 1.15rem !important; font-weight: 800; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; }
    .answer-structure ul { list-style: none; padding: 0; margin: 0; }
    .answer-structure li { margin-bottom: 18px; background: #f8f9fa; padding: 18px; border-radius: 10px; border-left: 5px solid #005691; }
    .answer-structure-title { font-weight: 700; color: #005691 !important; margin-bottom: 8px; font-size: 1.05rem !important;}
    .answer-structure-content { color: #475569 !important; font-size: 0.95rem !important; line-height: 1.6; }

    /* 🚨 채팅창 가로폭을 늘어난 상단 컨테이너 폭(1800px)에 완벽하게 맞춤 */
    div[data-testid="stChatInput"] { 
        max-width: 1800px !important;  
        margin: 0 auto !important; 
        left: 0 !important; right: 0 !important; 
        padding-bottom: 25px !important;
        background-color: #f8f9fa !important;
    }
    div[data-testid="stChatInput"] > div {
        margin: 0 3rem !important; /* 상단 컨테이너의 padding-left, right와 동일하게 맞춤 */
        border: 2px solid #cbd5e1 !important;
    }
    div[data-testid="stChatInput"] > div:focus-within { border-color: #005691 !important; }

    /* 모바일 반응형 */
    @media (max-width: 768px) {
        div[data-testid="column"]:nth-of-type(2) { display: none !important; }
        .block-container { padding-top: 0.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
        .dashboard-header { padding: 15px; margin-bottom: 15px; flex-direction: column; align-items: flex-start; gap: 10px;}
        .dashboard-header img { height: 35px !important; }
        .dashboard-header h1 { font-size: 1.3rem !important; }
        .welcome-section { padding: 20px; flex-direction: column; text-align: center; gap: 10px; margin-bottom: 15px;}
        div[data-testid="stButton"] button { font-size: 0.85rem !important; padding: 8px 12px !important; }
        div[data-testid="stChatInput"] { padding-bottom: 30px !important; }
        div[data-testid="stChatInput"] > div { margin: 0 1rem !important; }
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
        st.markdown(f"<h3 style='text-align:center; color:#003366; font-weight:800; margin-bottom:20px;'>{SYSTEM_NAME}</h3>", unsafe_allow_html=True)
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
    <h1>{SYSTEM_NAME}</h1>
</div>
""", unsafe_allow_html=True)

# 모드 선택
if "current_mode" not in st.session_state: st.session_state.current_mode = "🔍 인증 지침서 검색"
st.session_state.current_mode = st.radio("모드 선택", ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"], horizontal=True, label_visibility="collapsed")
mode = st.session_state.current_mode

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# 넓어진 가로폭에 맞춰 2분할 레이아웃 적용
main_col, answer_col = st.columns([2.2, 1], gap="large")

quick_query = None

SYS_RULE = f"""당신은 '{SYSTEM_NAME}'입니다. 
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
            <h2>안녕하세요! {SYSTEM_NAME}입니다</h2>
            <p>방대한 인증 지침서를 단 몇 초 만에 검색하고, AI 감독관과 함께 실전 훈련을 진행하세요.<br>지침 기반의 정확한 답변과 근거 페이지를 즉시 확인하시고 평가를 완벽하게 대비하십시오.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if mode == "🔍 인증 지침서 검색":
        st.markdown("<div class='quick-prompts-title'>💡 이렇게 질문해 보세요 (클릭 시 바로 검색됩니다)</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💬 낙상 발생 보고 절차 및 타임라인", use_container_width=True): quick_query = "낙상 발생 시 보고 절차와 타임라인은 어떻게 되나요?"
            if st.button("💬 감염관리 위원회 구성 요건과 역할", use_container_width=True): quick_query = "감염관리 위원회의 구성 요건과 주요 역할은 무엇인가요?"
            if st.button("💬 직원의 심폐소생술(CPR) 이수 기준", use_container_width=True): quick_query = "직원의 심폐소생술(CPR) 교육 이수 기준과 유효기간은?"
        with c2:
            if st.button("💬 근접오류(Near Miss) 보고 활성화", use_container_width=True): quick_query = "근접오류(Near Miss) 정의와 보고 활성화 방안은?"
            if st.button("💬 병동 환경 점검 필수 체크리스트", use_container_width=True): quick_query = "병동 환경 점검 체크리스트 필수 항목을 알려주세요."
            if st.button("💬 화재 발생 시 매뉴얼 (R.A.C.E.)", use_container_width=True): quick_query = "화재 발생 시 상황별 대응 매뉴얼(R.A.C.E.) 내용을 요약해줘."
        
        st.write("<br>", unsafe_allow_html=True)
        
        for m in st.session_state.search_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":
        st.info("💡 하단의 채팅창에 답변을 입력하면 AI가 지침서 기반으로 채점합니다.")
        if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
            with st.chat_message("assistant"):
                with st.spinner("💭 감독관이 지침서를 분석하여 질문을 생성 중..."):
                    random_docs = vdb.similarity_search(random.choice(["지침", "규정"]), k=3)
                    sample_ctx = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in random_docs])
                    q_stream = get_intelligent_response(f"인증평가 감독관 질문 1개 생성. 실제 현장에서 직원의 지침 숙지 여부를 묻는 날카로운 질문을 하세요.\n내용:\n{sample_ctx}")
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
                <div class='answer-structure-content'>핵심 내용을 2~3줄로 명확하게 요약하여 먼저 제시합니다.</div>
            </li>
            <li>
                <div class='answer-structure-title'>⚖️ 근거</div>
                <div class='answer-structure-content'>• 관련 지침서 항목 (예: 환자안전 지침서 3.4)<br>• 5주기 인증기준 번호<br>• 🚨 <strong>정확한 지침서 페이지 번호 (p.12)</strong></div>
            </li>
            <li>
                <div class='answer-structure-title'>📂 예상 확인자료</div>
                <div class='answer-structure-content'>조사위원이 현장에서 요구할 가능성이 높은 규정, 기록지, 보고서, 체크리스트 목록을 제시합니다.</div>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 하단 채팅창 (타이핑 입력값 또는 버튼 클릭값 모두 받음)
chat_input_query = st.chat_input("인증 지침에 관해 질문하거나 감독관의 질문에 답변하십시오...")

# 사용자가 직접 쳤거나, 버튼을 눌렀다면 둘 중 하나를 최종 검색어로 인식
final_query = chat_input_query or quick_query

if final_query:
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": final_query})
        with st.chat_message("user"): st.markdown(final_query)
        with st.chat_message("assistant"):
            with st.spinner("💭 지침서를 분석하며 답변을 정리 중..."):
                try:
                    docs = vdb.similarity_search(final_query, k=15)
                    ctx_str = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
                    full_ans = st.write_stream(get_intelligent_response(f"{SYS_RULE}\n\n[원문 데이터]\n{ctx_str}\n\n질문: {final_query}"))
                    st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
                except Exception as e: st.error(f"🚨 오류: {e}")
    else:
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": final_query})
            with st.chat_message("user"): st.markdown(final_query)
            with st.chat_message("assistant"):
                with st.spinner("💭 답변을 기반으로 지침서 부합 여부 채점 중..."):
                    try:
                        docs = vdb.similarity_search(st.session_state.current_q, k=10)
                        ctx_str = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
                        full_ans = st.write_stream(get_intelligent_response(f"인증평가 감독관 시선에서 직원의 답변 채점 및 보완. 실제 지침서 내용 기반 피드백.\n질문: {st.session_state.current_q}\n직원 답변: {final_query}\n지침 데이터:\n{ctx_str}"))
                        st.session_state.train_msgs.append({"role": "assistant", "content": full_ans})
                        st.session_state.current_q = None
                    except Exception as e: st.error(f"🚨 오류: {e}")
