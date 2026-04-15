import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
import random
import time
import base64

# ============================================================
# 🔑 Secrets 연동
# ============================================================
try:
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다.")
    st.stop()

SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증조사 AI 전문가", page_icon="🏅", layout="wide", initial_sidebar_state="auto")

# ============================================================
# 🎨 UI 고급화 CSS (모바일 드래그 현상 완벽 해결)
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    /* 앱 전체 배경 및 기본 글자색 (다크모드 방어) */
    .stApp { background-color: #F8FAFC !important; }
    p, span, div, li, h2, h3, h4 { color: #111827 !important; }
    
    /* 상단 메뉴 및 워터마크 은폐 */
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton { display: none !important; visibility: hidden !important; }
    
    /* 🚨 모바일 최적화: 여백을 최소화하여 네이티브 스크롤이 자연스럽게 작동하도록 수정 */
    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 6rem !important; /* 하단 입력창을 가리지 않게 여유 공간 확보 */
        margin-top: 0px !important; 
    }

    /* 초슬림 고급 헤더 */
    .enterprise-header { 
        background: linear-gradient(135deg, #002b5e 0%, #005691 100%); 
        padding: 12px 18px; 
        border-radius: 10px; 
        margin-top: 0px;
        margin-bottom: 5px;
        box-shadow: 0 4px 10px rgba(0, 86, 145, 0.1);
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .enterprise-header * { color: #ffffff !important; } 
    .enterprise-header h1 { margin: 0; font-size: 1.25rem !important; font-weight: 800; }
    .enterprise-header img { height: 26px !important; } 
    
    /* 탭 디자인 */
    button[data-baseweb="tab"] p { 
        font-size: 0.95rem !important; 
        font-weight: 700; 
        color: #111827 !important; 
        white-space: normal !important; 
        word-break: keep-all; 
        text-align: center; 
    }
    
    /* 🚨 억지로 붙이던 position: sticky 삭제. 스트림릿 네이티브 하단 고정 기능 활용 */
    [data-testid="stChatInput"] { 
        border: 2px solid #005691 !important; 
        border-radius: 20px !important; 
        background-color: #F8FAFC !important; 
    }
    [data-testid="stChatInput"] textarea { color: #111827 !important; }

    /* 채팅 말풍선 디자인 */
    [data-testid="stChatMessage"] { 
        background-color: #ffffff; 
        border-radius: 12px; 
        padding: 15px 20px; 
        box-shadow: 0 1px 4px rgba(0,0,0,0.05); 
        margin-bottom: 10px; 
        border: 1px solid #e2e8f0; 
    }
</style>
""", unsafe_allow_html=True)

# 🔐 로그인 페이지
if not st.session_state.get("authenticated", False):
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; font-weight:800; margin-bottom:20px;'>인증조사 AI 전문가</h3>", unsafe_allow_html=True)
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
    st.error(f"🚨 엔진 로딩 실패: {db_status_msg}")
    st.stop()

def get_intelligent_response(prompt_text):
    time.sleep(1.6)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=random.choice(API_KEYS),
        temperature=0.3 
    )
    for chunk in llm.stream(prompt_text):
        if chunk.content:
            yield chunk.content

# ============================================================
# 🗂️ 메인 시스템 UI
# ============================================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("### 📡 시스템 상태")
    st.success("인증 지침서 동기화 완료 (100%)")
    if db_status_msg: st.warning(db_status_msg)

logo_html = ""
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}' style='height:26px; background-color:white; padding:3px; border-radius:4px;'>"

st.markdown(f"""
<div class='enterprise-header'>
    {logo_html}
    <h1>검단탑병원 인증조사 AI 전문가</h1>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"])

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다. 사용자의 질문 유형에 따라 아래 두 가지 모드로 다르게 작동하십시오.

[모드 1: 일상 대화 및 인사]
- 사용자가 "안녕", "고마워", "수고했어", "넌 누구야?" 등 지침과 무관한 가벼운 대화를 건넬 때는 자연스럽고 친절하게 대화에 응하십시오.
- "저는 검단탑병원의 인증조사를 돕기 위해 학습된 AI 전문가입니다. 어떤 규정이 궁금하신가요?"와 같이 부드러운 톤을 유지하십시오.

[모드 2: 지침서 및 규정 질문 (엄격한 팩트 모드)]
- 병원 규정, 평가 기준, 업무 지침에 대한 질문이 들어오면, 즉시 감정을 배제하고 반드시 제공된 [원문 데이터]에만 근거하여 객관적으로 답변하십시오.
- 원문에 없는 내용은 절대 지어내지 마십시오.
- 두리뭉실한 답변을 피하고, 구체적인 절차나 기준을 불릿 기호(-, 1. 2.)를 사용하여 명확하게 정리하십시오."""

with tab1:
    # 🚨 억지로 고정하던 400px 상자 삭제. 자연스러운 화면 스크롤 적용.
    for m in st.session_state.search_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정 질문 또는 가볍게 인사를 건네보세요...", key="q_search"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        
        with st.chat_message("assistant"):
            try:
                docs = vdb.similarity_search(query, k=5)
                ctx = "\n\n".join([f"[근거 {i+1}]: {d.page_content}" for i, d in enumerate(docs)])
                
                res_stream = get_intelligent_response(f"{SYS_RULE}\n\n[원문 데이터]\n{ctx}\n\n사용자 입력: {query}")
                full_ans = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
            except Exception as e:
                st.error(f"🚨 답변 생성 오류: {e}")

with tab2:
    st.info("💡 모의 감독관이 무작위로 던지는 현장 질문에 답변하여 채점을 받아보세요.")
    
    # 🚨 억지로 고정하던 400px 상자 삭제.
    for m in st.session_state.train_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])
        
    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        with st.chat_message("assistant"):
            try:
                q_stream = get_intelligent_response("병원 인증평가 감독관이 현장 직원에게 던질법한 날카로운 질문 1개만 생성하시오. (인사말 생략)")
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
                    eval_p = f"당신은 엄격한 인증평가 감독관입니다. [원문]에 근거하여 직원의 답변을 100점 만점으로 채점하고, 누락된 내용을 보완하여 설명해줘.\n\n질문: {st.session_state.current_q}\n직원 답변: {ans_input}\n원문:\n{ctx}"
                    res_stream = get_intelligent_response(eval_p)
                    eval_ans = st.write_stream(res_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": eval_ans})
                    st.session_state.current_q = None
                except Exception as e:
                    st.error(f"🚨 채점 오류: {e}")
