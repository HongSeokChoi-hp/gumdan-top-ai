import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

# ============================================================
# 🔑 1. API 키 설정 (여기에 기획자님 키를 직접 넣으세요)
# ============================================================
MY_KEY = "AIzaSyCc6eH7IU47TKCYWJ5H4OUzh1sFz8O9uzM" # <--- 여기에 키 입력
SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증 AI 마스터", page_icon="🏅", layout="wide", initial_sidebar_state="collapsed")

# ============================================================
# 🎨 2. 거머리 로고 및 스트림릿 찌꺼기 완전 삭제 (초강력 CSS)
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 🚫 스트림릿 기본 로고, 메뉴, 하단 배지 영구 삭제 */
    header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"] {visibility: hidden !important; display: none !important;}
    .viewerBadge_container__1QSob, #viewerBadge, div[class*="viewerBadge"], a[href*="streamlit.io"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}

    /* UI 레이아웃 최적화 */
    .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
    .enterprise-header { background: linear-gradient(135deg, #003366 0%, #005691 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 15px;}
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; font-weight: 900; color: white;}
</style>
""", unsafe_allow_html=True)

# 🔐 로그인 화면 (비밀번호 예시 삭제 완료)
if not st.session_state.get("authenticated", False):
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; font-weight:800;'>인증 AI 마스터 접속</h3>", unsafe_allow_html=True)
        pwd = st.text_input("보안코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: 
            st.session_state.authenticated = True
            st.rerun()
        elif pwd: st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🧠 3. 핵심 엔진 (404 에러 방지용 최적화)
# ============================================================
def get_answer(prompt_text):
    genai.configure(api_key=MY_KEY)
    # 404 에러를 방지하기 위해 가장 안정적인 모델 호출 방식을 사용합니다.
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content(prompt_text, stream=False)
        return response.text
    except Exception as e:
        return f"❌ AI 엔진 연결 오류: {str(e)}"

@st.cache_resource
def load_db():
    if not os.path.exists("faiss_index_saved"): return None
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=MY_KEY)
        return FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
    except: return None

st.markdown("<div class='enterprise-header'><h1>🏅 검단탑병원 인증조사 마스터 AI</h1></div>", unsafe_allow_html=True)

vdb = load_db()
if vdb is None: st.error("🚨 지식 데이터(faiss_index_saved)를 불러올 수 없습니다. 폴더 업로드 상태를 확인하세요."); st.stop()

# ============================================================
# 🗂️ 4. 답변 로직 (철저하게 자료 기반)
# ============================================================
if "msgs" not in st.session_state: st.session_state.msgs = []

# AI에게 절대 지어내지 말라고 다시 한번 강력하게 경고했습니다.
SYS_PROMPT = """당신은 검단탑병원 인증평가 전문 컨설턴트입니다. 
규칙: 
1. 오직 아래 [지침서 원문]의 내용만 사용하여 답변하세요. 
2. 자료에 없는 내용을 물어보면 절대 소설을 쓰지 말고 "지침서에서 관련 내용을 찾을 수 없습니다."라고만 하세요.
3. 답변은 번호를 매겨 깔끔하게 요약하세요.
"""

chat_box = st.container(height=450)
for m in st.session_state.msgs:
    with chat_box.chat_message(m["role"]): st.markdown(m["content"])

if query := st.chat_input("규정이나 지침을 질문하십시오..."):
    st.session_state.msgs.append({"role": "user", "content": query})
    with chat_box.chat_message("user"): st.markdown(query)
    
    with chat_box.chat_message("assistant"):
        with st.spinner("지침서 정밀 분석 중..."):
            docs = vdb.similarity_search(query, k=4)
            ctx = "\n\n".join([d.page_content for d in docs])
            ans = get_answer(f"{SYS_PROMPT}\n\n[지침서 원문]\n{ctx}\n\n질문: {query}")
            st.markdown(ans)
            st.session_state.msgs.append({"role": "assistant", "content": ans})
