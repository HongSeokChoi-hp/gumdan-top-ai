import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from PIL import Image

# ============================================================
# 🔑 1. API 키 설정 (여기에 직접 넣으시면 가장 확실합니다)
# ============================================================
# [필독] 아래 따옴표 안에 기획자님의 API 키를 직접 붙여넣으세요.
MY_KEY = "AIzaSyCc6eH7IU47TKCYWJ5H4OUzh1sFz8O9uzM" 

SET_PASSWORD = "0366" 

# ============================================================
# 🎨 2. 디자인 및 거머리 로고/배지 완전 박멸 (무적의 CSS)
# ============================================================
st.set_page_config(page_title="검단탑병원 인증 AI", page_icon="🏅", layout="wide")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    /* 🚫 스트림릿 잔재물(상단 메뉴, 연필, 깃허브, 로고) 영원히 제거 */
    header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"] {visibility: hidden; display: none !important;}
    
    /* 🔥 [필독] 모바일/PC 우측 하단 끈질긴 빨간 배지/프로필 강제 파괴 */
    div[data-testid="stStatusWidget"], .viewerBadge_container__1QSob, #viewerBadge, div[class*="viewerBadge"] {display: none !important; visibility: hidden !important;}
    a[href*="streamlit.io"] {display: none !important;}
    iframe {display: none !important;}

    .stApp { background-color: #f8fafc; }
    .enterprise-header { 
        background: linear-gradient(135deg, #003366 0%, #005691 100%); 
        color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px;
    }
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; color: white; font-weight: 900;}
</style>
""", unsafe_allow_html=True)

# 로고 안전 로드 (파일명 달라도 앱 안터짐)
def load_logo():
    path = "검단탑병원-로고_고화질.png"
    try:
        if os.path.exists(path):
            st.image(Image.open(path), use_container_width=True)
        else:
            st.markdown("<h2 style='color:#003366; text-align:center;'>🏥 검단탑병원 인증 AI</h2>", unsafe_allow_html=True)
    except:
        st.markdown("<h2 style='color:#003366; text-align:center;'>🏥 검단탑병원</h2>", unsafe_allow_html=True)

# 🔐 로그인 
if not st.session_state.get("authenticated", False):
    st.write("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        load_logo()
        pwd = st.text_input("보안코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: 
            st.session_state.authenticated = True
            st.rerun()
        elif pwd: st.error("❌ 보안 코드가 틀립니다.")
    st.stop()

# ============================================================
# 🧠 3. 핵심 엔진
# ============================================================
def get_answer(prompt_text):
    genai.configure(api_key=MY_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"❌ 오류 발생: {str(e)}"

@st.cache_resource
def load_db():
    if not os.path.exists("faiss_index_saved"): return None
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=MY_KEY)
        return FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
    except: return None

vdb = load_db()
if vdb is None: st.error("🚨 지식 데이터를 불러올 수 없습니다. (faiss_index_saved 폴더 확인 필요)"); st.stop()

# ============================================================
# 🗂️ 4. 메인 화면
# ============================================================
st.markdown("<div class='enterprise-header'><h1>🏅 검단탑병원 인증조사 마스터</h1></div>", unsafe_allow_html=True)

if "msgs" not in st.session_state: st.session_state.msgs = []

chat_box = st.container(height=450)
for m in st.session_state.msgs:
    with chat_box.chat_message(m["role"]): st.markdown(m["content"])

if query := st.chat_input("질문을 입력하십시오..."):
    st.session_state.msgs.append({"role": "user", "content": query})
    with chat_box.chat_message("user"): st.markdown(query)
    
    with chat_box.chat_message("assistant"):
        with st.spinner("지침서 분석 중..."):
            docs = vdb.similarity_search(query, k=4)
            ctx = "\n\n".join([d.page_content for d in docs])
            
            prompt = f"지침서 내용:\n{ctx}\n\n질문: {query}\n(자료에 있는 내용만 번호 매겨 대답할 것. 자료에 없으면 모른다고 하세요.)"
            
            ans = get_answer(prompt)
            st.markdown(ans)
            st.session_state.msgs.append({"role": "assistant", "content": ans})
