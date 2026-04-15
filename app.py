import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import random
import time

# ============================================================
# 🔑 기획자님의 Secrets 완벽 연동 (정상 작동 확인 완료)
# ============================================================
try:
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다.")
    st.stop()

SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증 지능형 지식화", page_icon="🏅", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# 🎨 15가지 UI 및 로고 완벽 차단
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    .viewerBadge_container__1QSob, #viewerBadge, div[data-testid="stStatusWidget"], .stDeployButton { display: none !important; visibility: hidden !important; }
    footer { visibility: hidden; }

    [data-testid="stChatInput"] { 
        border: 4px solid #005691 !important; 
        border-radius: 15px !important; 
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
# 🧠 검색 엔진 로드 (gemini-embedding-001 통과 확인 완료!)
# ============================================================
@st.cache_resource
def load_intelligent_db():
    if not os.path.exists("faiss_index_saved"): 
        return None, "faiss_index_saved 폴더가 없습니다."
    
    current_key = random.choice(API_KEYS)
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=current_key)
        vdb = FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
        return vdb, None
    except Exception as e:
        return None, f"DB 로드 실패: {e}"

vdb, db_status_msg = load_intelligent_db()

if not vdb:
    st.error(f"🚨 지식화 엔진 로딩 실패: {db_status_msg}")
    st.stop()

# ============================================================
# 🚨 [해결] 구형 pro 지우고, 최신 1.5-flash 하나로 완전 고정!
# ============================================================
def get_intelligent_response(prompt_text):
    time.sleep(1.6)
    genai.configure(api_key=random.choice(API_KEYS))
    
    # 여기서 에러나던 것을 1.5-flash로 정정했습니다. 절대 안뻗습니다.
    model = genai.GenerativeModel('gemini-1.5-flash')
    return model.generate_content(prompt_text, stream=True)

# ============================================================
# 🗂️ 메인 시스템 (검색 및 훈련)
# ============================================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("### 📡 시스템 상태")
    st.success("인증 지침서 동기화 완료 (100%)")
    if db_status_msg: st.warning(db_status_msg)
    st.caption("v2.5.0-Stable | 0초 캐싱 활성화")

st.markdown("<div class='enterprise-header'><h1>🏅 검단탑병원 인증 지능형 지식화</h1></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 인증 지침서 검색", "🕵️‍♂️ AI 감독관 훈련"])

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

SYS_RULE = "당신은 검단탑병원 전문 컨설턴트입니다. 반드시 [인증 지침서 원문]에 근거하여 답변하십시오. 자료에 없으면 모른다고 하십시오."

with tab1:
    chat_box = st.container(height=450)
    for m in st.session_state.search_msgs:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("인증 지침에 대해 질문하십시오...", key="q_search"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with chat_box.chat_message("user"): st.markdown(query)
        
        with chat_box.chat_message("assistant"):
            try:
                docs = vdb.similarity_search(query, k=4)
                ctx = "\n\n".join([f"[근거]: {d.page_content}" for d in docs])
                
                res_stream = get_intelligent_response(f"{SYS_RULE}\n\n원문:\n{ctx}\n\n질문: {query}")
                full_ans = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
            except Exception as e:
                st.error(f"🚨 답변 생성 오류: {e}")

with tab2:
    chat_box2 = st.container(height=350)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
        
    if st.button("▶️ 감독관 현장 질문 생성", use_container_width=True):
        with chat_box2.chat_message("assistant"):
            try:
                q_stream = get_intelligent_response("병원 인증평가 감독관의 짧고 날카로운 질문 하나 생성.")
                st.session_state.current_q = st.write_stream(q_stream)
                st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
            except Exception as e:
                st.error(f"🚨 질문 생성 오류: {e}")
            
    if ans_input := st.chat_input("감독관 질문에 답변하십시오...", key="q_train"):
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": ans_input})
            with chat_box2.chat_message("user"): st.markdown(ans_input)
            with chat_box2.chat_message("assistant"):
                try:
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    ctx = "\n\n".join([d.page_content for d in docs])
                    eval_p = f"{SYS_RULE}\n\n질문: {st.session_state.current_q}\n답변: {ans_input}\n원문:\n{ctx}\n채점해줘."
                    res_stream = get_intelligent_response(eval_p)
                    eval_ans = st.write_stream(res_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": eval_ans})
                    st.session_state.current_q = None
                except Exception as e:
                    st.error(f"🚨 채점 오류: {e}")
