import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import random

# ============================================================
# 🎨 1. [디자인] 거머리 로고 완전 소각 및 깔끔한 UI
# ============================================================
SET_PASSWORD = "0366" 
st.set_page_config(page_title="검단탑병원 인증 AI 마스터", page_icon="🏅", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 🚫 스트림릿 잔재물(로고, 배지, 메뉴) 물리적 파괴 */
    header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stStatusWidget"] {visibility: hidden !important; display: none !important;}
    .viewerBadge_container__1QSob, .viewerBadge_link__1S137, #viewerBadge, a[href*="streamlit.io"] {display: none !important;}

    /* 레이아웃 최적화 */
    .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
    .enterprise-header { background: linear-gradient(135deg, #003366 0%, #005691 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 15px;}
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; font-weight: 900; color: white;}
</style>
""", unsafe_allow_html=True)

# [수정] 기획자님이 처음부터 사용하신 파일명으로 직접 호출
def show_hospital_logo():
    logo_path = "검단탑병원-로고_고화질.png"
    try:
        if os.path.exists(logo_path):
            st.image(logo_path, use_container_width=True)
        else:
            st.warning(f"⚠️ {logo_path} 파일을 찾을 수 없습니다. 깃허브 업로드 상태를 확인해주세요.")
    except Exception:
        # 파일은 있으나 서버 에러(한글 인코딩 등)로 못 읽을 경우 앱이 터지지 않게 보호
        st.markdown("<h2 style='color:#003366; text-align:center;'>🏥 검단탑병원</h2>", unsafe_allow_html=True)

if not st.session_state.get("authenticated", False):
    st.write("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        show_hospital_logo() # 로고 출력
        pwd = st.text_input("보안코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        elif pwd: st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🔑 2. 최적화 엔진 (모델명: gemini-1.5-flash)
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

def generate_answer(prompt_text):
    genai.configure(api_key=API_KEYS[0])
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content(prompt_text, stream=False)
        return response.text
    except Exception as e:
        return f"❌ 시스템 오류: {str(e)}"

# ============================================================
# 📚 3. 0초 데이터 로딩
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
if error_msg: st.error("🚨 데이터 로드 실패: " + error_msg); st.stop()

# ============================================================
# 🗂️ 4. 답변 로직 (철저하게 자료 기반)
# ============================================================
if "msgs" not in st.session_state: st.session_state.msgs = []

SYS_PROMPT = """당신은 검단탑병원 인증평가 도우미입니다. 
규칙: 
1. 오직 아래 [지침서 원문]에 있는 내용만 사용하여 답변하십시오. 
2. 자료에 없는 내용을 물어보면 절대 소설을 쓰지 말고 "지침서에서 관련 내용을 찾을 수 없습니다."라고만 하십시오.
3. 답변은 번호를 매겨서 정중하게 하십시오.
"""

chat_box = st.container(height=450)
for m in st.session_state.msgs:
    with chat_box.chat_message(m["role"]): st.markdown(m["content"])

if query := st.chat_input("규정이나 지침을 질문하십시오..."):
    st.session_state.msgs.append({"role": "user", "content": query})
    with chat_box.chat_message("user"): st.markdown(query)
    
    with chat_box.chat_message("assistant"):
        with st.spinner("지침서를 정밀 분석 중입니다..."):
            docs = vdb.similarity_search(query, k=4)
            ctx = "\n\n".join([d.page_content for d in docs])
            ans = generate_answer(f"{SYS_PROMPT}\n\n[지침서 원문]\n{ctx}\n\n질문: {query}")
            st.markdown(ans)
            st.session_state.msgs.append({"role": "assistant", "content": ans})
