import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import random
import time

# ============================================================
# 🔑 [1, 5] API 키 로테이션 및 보안 인증
# ============================================================
API_KEYS = ["여기에_API_키_입력"] # 기획자님 키 입력 필수
SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증 지능형 지식화", page_icon="🏅", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# 🎨 [2, 3, 4] UI 고도화 및 거머리 로고 차단
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 거머리 배지/로고 정밀 타격 제거 */
    .viewerBadge_container__1QSob, #viewerBadge, .stDeployButton { display: none !important; }
    footer { visibility: hidden; }

    /* 검색창 진한 파란색 4px 테두리 */
    [data-testid="stChatInput"] { 
        border: 4px solid #005691 !important; 
        border-radius: 15px !important; 
        box-shadow: 0 5px 15px rgba(0, 86, 145, 0.2) !important;
    }

    /* 반응형 여백 조절 */
    @media (max-width: 768px) {
        .block-container { padding-top: 0rem !important; }
        .enterprise-header h1 { font-size: 1.4rem !important; }
        header { display: none !important; }
    }
    
    .enterprise-header { background: linear-gradient(135deg, #003366 0%, #005691 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 15px; }
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("authenticated", False):
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        pwd = st.text_input("인증코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        elif pwd: st.error("❌ 인증 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🧠 [해결 핵심] 구글 공식 임베딩 모델명으로 정확히 수정 (오타 제거)
# ============================================================
@st.cache_resource
def load_intelligent_db():
    if not os.path.exists("faiss_index_saved"): return None
    try:
        # 🚨 [수정 완료] models/gemini-embedding-001 -> models/embedding-001 로 정정
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=random.choice(API_KEYS))
        return FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        st.error(f"지식화 엔진 로딩 실패: {e}")
        return None

vdb = load_intelligent_db()

def get_intelligent_response(prompt_text):
    time.sleep(1.6) # 서버 보호 1.6초 휴식
    selected_key = random.choice(API_KEYS)
    genai.configure(api_key=selected_key)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model.generate_content(prompt_text, stream=True)
    except:
        model = genai.GenerativeModel('gemini-1.5-pro')
        return model.generate_content(prompt_text, stream=True)

# ============================================================
# 🗂️ 메인 시스템 (검색 / 훈련)
# ============================================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("### 📡 시스템 상태")
    if vdb: st.success("인증 지침서 데이터 동기화 완료 (100%)")
    st.caption("v1.5.0-Stable | 0초 캐싱 활성화")

st.markdown("<div class='enterprise-header'><h1>🏅 검단탑병원 인증 지능형 지식화</h1></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 인증 지침서 검색", "🕵️‍♂️ AI 감독관 훈련"])

if "msgs" not in st.session_state: st.session_state.msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

SYS_RULE = "당신은 검단탑병원 전문 컨설턴트입니다. 반드시 [인증 지침서 원문]에 근거하여 답변하십시오. 자료에 없으면 모른다고 하십시오."

with tab1:
    chat_box = st.container(height=450)
    for m in st.session_state.msgs:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("인증 지침에 대해 질문하십시오..."):
        st.session_state.msgs.append({"role": "user", "content": query})
        with chat_box.chat_message("user"): st.markdown(query)
        
        with chat_box.chat_message("assistant"):
            docs = vdb.similarity_search(query, k=4)
            ctx = "\n\n".join([f"[근거]: {d.page_content}" for d in docs])
            
            res_stream = get_intelligent_response(f"{SYS_RULE}\n\n원문:\n{ctx}\n\n질문: {query}")
            full_ans = st.write_stream(res_stream)
            st.session_state.msgs.append({"role": "assistant", "content": full_ans})

with tab2:
    if st.button("▶️ 감독관 현장 질문 생성", use_container_width=True):
        with st.chat_message("assistant"):
            q_stream = get_intelligent_response("병원 인증평가 감독관의 짧고 날카로운 질문 하나 생성.")
            st.session_state.current_q = st.write_stream(q_stream)
            
    if ans_input := st.chat_input("감독관 질문에 답변하십시오..."):
        if st.session_state.current_q:
            with st.chat_message("user"): st.markdown(ans_input)
            with st.chat_message("assistant"):
                docs = vdb.similarity_search(st.session_state.current_q, k=3)
                ctx = "\n\n".join([d.page_content for d in docs])
                eval_p = f"{SYS_RULE}\n\n질문: {st.session_state.current_q}\n답변: {ans_input}\n원문:\n{ctx}\n채점해줘."
                st.write_stream(get_intelligent_response(eval_p))
                st.session_state.current_q = None
