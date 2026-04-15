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
# 🎨 UI 고급화 CSS (누락된 디테일 완벽 복구)
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    /* 배경 및 다크모드 무력화 (흰 배경에 검은 글씨) */
    .stApp { background-color: #F8FAFC !important; }
    p, span, div, li, h2, h3, h4 { color: #111827 !important; }
    
    /* 스트림릿 기본 찌꺼기 은폐 */
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton { display: none !important; visibility: hidden !important; }
    
    /* 모바일 상단 태평양 여백 제거 */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; margin-top: 0px !important; }

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
    .enterprise-header * { color: #ffffff !important; } /* 배너 안은 100% 흰글씨 */
    .enterprise-header h1 { margin: 0; font-size: 1.25rem !important; font-weight: 800; }
    .enterprise-header img { height: 26px !important; } 
    
    /* 🚨 [복구] 모바일 탭 글씨 짤림 방지 (자동 줄바꿈) */
    button[data-baseweb="tab"] p { 
        font-size: 0.95rem !important; 
        font-weight: 700; 
        color: #111827 !important; 
        white-space: normal !important; 
        word-break: keep-all; 
        text-align: center; 
    }
    
    /* 🚨 [복구] 카톡 스타일 입력창 밑바닥 본드 고정 */
    [data-testid="stChatInput"] { 
        border: 2px solid #005691 !important; 
        border-radius: 20px !important; 
        position: sticky !important; 
        bottom: 0 !important; 
        background-color: #F8FAFC !important; 
        z-index: 9999 !important; 
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
        temperature=0.3 # 일상 대화의 유연성과 지침의 정확도를 잡는 황금비율
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

# 🚨 이중 모드 스위치 프롬프트 (유지)
SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다. 사용자의 질문 유형에 따라 아래 두 가지 모드로 다르게 작동하십시오.

[모드 1: 일상 대화 및 인사]
- 사용자가 "안녕", "고마워", "수고했어", "넌 누구야?" 등 지침과 무관한 가벼운 대화를 건넬 때는 자연스럽고 친절하게 대화에 응하십시오.
- "저는 검단탑병원의 인증조사를 돕기 위해 학습된 AI 전문가입니다. 어떤 규정이 궁금하신가요?"와 같이 부드러운 톤을 유지하십시오.

[모드 2: 지침서 및 규정 질문 (엄격한 팩트 모드)]
- 병원 규정, 평가 기준, 업무 지침에 대한 질문이 들어오면, 즉시 감정을 배제하고 반드시 제공된 [원문 데이터]에만 근거하여 객관적으로 답변하십시오.
- 원문에 없는 내용은 절대 지어내지 마십시오.
- 두리뭉실한 답변을 피하고, 구체적인 절차나 기준을 불릿 기호(-, 1. 2.)를 사용하여 명확하게 정리하십시오."""

with tab1:
    # 🚨 한 화면 최적화 세팅 (유지)
    chat_box = st.container(height=400, border=False)
    
    for m in st.session_state.search_msgs:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정 질문 또는 가
