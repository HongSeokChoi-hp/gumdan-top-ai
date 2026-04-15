import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
import random
import time

# ============================================================
# 🔑 Secrets 완벽 연동
# ============================================================
try:
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다.")
    st.stop()

SET_PASSWORD = "0366" 

# [수정 1] PC에서는 사이드바가 열려있고, 모바일은 자동 숨김되는 정석 세팅
st.set_page_config(page_title="검단탑병원 지능형 지식화", page_icon="🏅", layout="wide", initial_sidebar_state="auto")

# ============================================================
# 🎨 UI 고급화 및 색상/레이아웃 버그 완벽 수정
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    /* [수정 4] 배경색과 글자색 명확히 고정 (흰 바탕에 까만 글씨) */
    .stApp { background-color: #F0F4F8; color: #111827 !important; }
    p, span, div, li { color: #111827; }
    
    /* 상단 기본 메뉴바 숨김 (공식 지원 범위 내 최대한의 깔끔함) */
    [data-testid="stHeader"] { background-color: transparent; }

    /* 입력창 카톡 스타일 고급화 (하단 고정) */
    [data-testid="stChatInput"] { 
        border: 2px solid #005691 !important; 
        border-radius: 20px !important; 
        box-shadow: 0 -4px 20px rgba(0,0,0,0.05) !important;
        background-color: white !important;
    }

    /* 상단 배너 디자인 (글씨는 무조건 흰색) */
    .enterprise-header { 
        background: linear-gradient(135deg, #002b5e 0%, #005691 100%); 
        padding: 20px 25px; 
        border-radius: 12px; 
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(0, 86, 145, 0.15);
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .enterprise-header h1 { margin: 0; font-size: 1.6rem; font-weight: 800; color: #ffffff !important; }
    
    /* [수정 5] 모바일 탭 글씨 안 잘리게 자동 줄바꿈 처리 */
    button[data-baseweb="tab"] p { 
        font-size: 1rem !important; 
        font-weight: 700; 
        white-space: normal !important; /* 자동 줄바꿈 핵심 */
        text-align: center;
    }
    
    /* 챗봇 말풍선 디자인 (가독성 극대화) */
    [data-testid="stChatMessage"] { 
        background-color: #ffffff; 
        border-radius: 12px; 
        padding: 15px 20px; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.03); 
        margin-bottom: 12px; 
        border: 1px solid #e2e8f0; 
    }
</style>
""", unsafe_allow_html=True)

# 🔐 로그인 페이지
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; font-weight:800; margin-bottom:20px;'>인증 지능형 지식화 시스템</h3>", unsafe_allow_html=True)
        pwd = st.text_input("인증코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        elif pwd: st.error("❌ 인증 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🧠 검색 엔진 로드
# ============================================================
@st.cache_resource
def load_intelligent_db():
    if not os.path.exists("faiss_index_saved"): 
        return None, "faiss_index_saved 폴더가 없습니다."
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=random.choice(API_KEYS))
        vdb = FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
        return vdb, None
    except Exception as e:
        return None, f"DB 로드 실패: {e}"

vdb, db_status_msg = load_intelligent_db()

if not vdb:
    st.error(f"🚨 지식화 엔진 로딩 실패: {db_status_msg}")
    st.stop()

def get_intelligent_response(prompt_text):
    time.sleep(1.6)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=random.choice(API_KEYS),
        temperature=0.0 
    )
    for chunk in llm.stream(prompt_text):
        if chunk.content:
            yield chunk.content

# ============================================================
# 🗂️ 메인 시스템 UI (PC/모바일 반응형 분리)
# ============================================================
# 사이드바 (PC에서는 열림, 모바일에서는 햄버거 메뉴로 자동 숨김)
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("### 📡 시스템 상태")
    st.success("인증 지침서 동기화 완료 (100%)")
    if db_status_msg: st.warning(db_status_msg)
    st.caption("v2.5.0-Stable | 반응형 UI 적용 완료")

# 상단 메인 헤더
st.markdown("""
<div class='enterprise-header'>
    <h1>🏅 검단탑병원 인증 지능형 지식화</h1>
</div>
""", unsafe_allow_html=True)

# 탭 구조 (모바일 글씨 짤림 방지 적용)
tab1, tab2 = st.tabs(["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"])

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

SYS_RULE = """당신은 검단탑병원 인증평가 최고 책임 컨설턴트입니다.
반드시 제공된 [인증 지침서 원문]에만 근거하여 답변하십시오. 원문에 없는 내용은 절대 지어내지 마십시오.
[지시사항]
1. 두리뭉실한 답변을 금지합니다.
2. 지침서 내의 '구체적인 절차, 예외 상황, 기준 수치 및 예시'를 빠짐없이 추출하십시오.
3. 읽기 쉽게 불릿 기호(-, *, 1. 2. 3.)를 사용하여 체계적이고 상세하게 설명하십시오."""

with tab1:
    # [수정 3] 고정된 박스(container) 제거. 이러면 전체 화면을 쓰면서 카톡처럼 아래로 입력창이 고정됩니다.
    for m in st.session_state.search_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정이나 지침에 대해 질문하십시오...", key="q_search"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        
        with st.chat_message("assistant"):
            try:
                docs = vdb.similarity_search(query, k=5)
                ctx = "\n\n".join([f"[근거 {i+1}]: {d.page_content}" for i, d in enumerate(docs)])
                
                res_stream = get_intelligent_response(f"{SYS_RULE}\n\n[원문 데이터]\n{ctx}\n\n질문: {query}")
                full_ans = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
            except Exception as e:
                st.error(f"🚨 답변 생성 오류: {e}")

with tab2:
    st.info("💡 모의 감독관이 무작위로 던지는 현장 질문에 답변하여 채점을 받아보세요.")
    for m in st.session_state.train_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])
        
    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        with st.chat_message("assistant"):
            try:
                q_stream = get_intelligent_response("병원 인증평가 감독관이 현장 직원에게 던질법한 날카로운 질문 1개만 생성하시오.")
                st.session_state.current_q = st.write_stream(q_stream)
                st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
            except Exception as e:
                st.error(f"🚨 질문 생성 오류: {e}")
            
    if ans_input := st.chat_input("감독관 질문에 답변하십시오...", key="q_train"):
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": ans_input})
            with st.chat_message("user"): st.markdown(ans_input)
            with st.chat_message("assistant"):
                try:
                    docs = vdb.similarity_search(st.session_state.current_q, k=4)
                    ctx = "\n\n".join([d.page_content for d in docs])
                    eval_p = f"{SYS_RULE}\n\n질문: {st.session_state.current_q}\n직원 답변: {ans_input}\n원문:\n{ctx}\n\n이 답변을 지침서 기반으로 엄격하게 채점(100점 만점)하고, 누락된 핵심 내용을 상세히 보완하여 설명해줘."
                    res_stream = get_intelligent_response(eval_p)
                    eval_ans = st.write_stream(res_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": eval_ans})
                    st.session_state.current_q = None
                except Exception as e:
                    st.error(f"🚨 채점 오류: {e}")
