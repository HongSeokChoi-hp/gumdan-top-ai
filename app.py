import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import random

# ============================================================
# 🎨 1. [디자인/보안] 병원 전용 UI 및 거머리 로고 완전 박멸
# ============================================================
SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증 AI 마스터", page_icon="🏅", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 🚫 스트림릿 기본 UI/로고/배지 완전 소각 */
    header, footer, #MainMenu, [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    
    /* 🔥 [필독] 우측 하단 빨간 로고/프로필/배지 강제 삭제 */
    div[data-testid="stStatusWidget"], .viewerBadge_container__1QSob, .viewerBadge_link__1S137, #viewerBadge, [data-testid="stActionButtonIcon"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* 스트림릿 링크가 걸린 모든 요소를 화면 밖으로 */
    a[href*="streamlit.io"] { display: none !important; }

    /* 상단 빈 공간 제거 */
    .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
    .enterprise-header { background: linear-gradient(135deg, #003366 0%, #005691 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 15px;}
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; color: white; font-weight: 900;}
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("authenticated", False):
    st.write("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고_화질.png", use_container_width=True)
        pwd = st.text_input("보안코드", type="password", placeholder="코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        elif pwd: st.error("❌ 비밀번호 오류")
    st.stop()

# ============================================================
# 🔑 2. 정답 엔진 (모델명: gemini-1.5-flash로 수정 완료)
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

def generate_answer(prompt_text):
    # 404 방지를 위해 가장 확실한 모델명을 사용합니다.
    genai.configure(api_key=API_KEYS[0])
    model = genai.GenerativeModel('gemini-1.5-flash') 
    try:
        response = model.generate_content(prompt_text, stream=False)
        return response.text
    except Exception as e:
        return f"❌ 오류 발생: {str(e)}"

# ============================================================
# 📚 3. 지식 로딩
# ============================================================
@st.cache_resource
def load_vdb():
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=API_KEYS[0])
        return FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True), None
    except Exception as e:
        return None, str(e)

st.markdown("<div class='enterprise-header'><h1>🏅 검단탑병원 인증조사 AI</h1></div>", unsafe_allow_html=True)

vdb, error_msg = load_vdb()
if error_msg: st.error("데이터 로드 실패: " + error_msg); st.stop()

# ============================================================
# 🗂️ 4. 답변 로직 (철저하게 자료 기반)
# ============================================================
if "msgs" not in st.session_state: st.session_state.msgs = []

SYS_PROMPT = """당신은 검단탑병원 인증평가 도우미입니다. 
규칙: 
1. 오직 아래 [지침서 원문]에 있는 내용만 대답하세요. 
2. 자료에 없는 내용을 물어보면 "지침서에서 관련 내용을 찾을 수 없습니다."라고만 하세요. 절대 지어내지 마세요.
3. 답변은 번호를 매겨서 간결하게 하세요.
"""

chat_box = st.container(height=450)
for m in st.session_state.msgs:
    with chat_box.chat_message(m["role"]): st.markdown(m["content"])

if query := st.chat_input("질문을 입력하세요..."):
    st.session_state.msgs.append({"role": "user", "content": query})
    with chat_box.chat_message("user"): st.markdown(query)
    
    with chat_box.chat_message("assistant"):
        with st.spinner("자료 검색 중..."):
            docs = vdb.similarity_search(query, k=4)
            ctx = "\n\n".join([d.page_content for d in docs])
            ans = generate_answer(f"{SYS_PROMPT}\n\n[지침서 원문]\n{ctx}\n\n질문: {query}")
            st.markdown(ans)
            st.session_state.msgs.append({"role": "assistant", "content": ans})
