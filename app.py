import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import time

# ==========================================
# 🔐 보안 및 초기 설정
# ==========================================
SET_PASSWORD = "0366"
st.set_page_config(page_title="검단탑병원 인증 AI", page_icon="🏅", layout="wide")

# CSS: 카카오톡 스타일 UI 및 고정 입력창
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px;
    }
    .stChatMessage { border-radius: 10px; margin-bottom: 10px; border: 1px solid #e1e4e8; }
</style>
""", unsafe_allow_html=True)

# 비밀번호 체크
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"):
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        pwd = st.text_input("보안 접근 코드를 입력하십시오.", type="password")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# API 설정
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# ==========================================
# 📚 RAG 엔진: PDF 쪼개기 및 인덱싱 (핵심)
# ==========================================
@st.cache_resource
def build_vector_db():
    all_text = ""
    pdf_files = ["guide.pdf", "manual2.pdf"]
    
    # 1. PDF에서 텍스트 추출
    progress_bar = st.progress(0)
    st.write("📡 시스템 가동 중: 600페이지 지침서를 인덱싱하고 있습니다. (최초 1회만 소요)")
    
    for idx, file in enumerate(pdf_files):
        if os.path.exists(file):
            reader = PdfReader(file)
            for page in reader.pages:
                all_text += page.extract_text()
        progress_bar.progress((idx + 1) / len(pdf_files))
    
    # 2. 텍스트 조각내기 (Chunking)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = text_splitter.split_text(all_text)
    
    # 3. 벡터 DB 생성 (무료 구글 임베딩 사용)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    vector_db = FAISS.from_texts(chunks, embeddings)
    
    progress_bar.empty()
    return vector_db

# 엔진 가동
vdb = build_vector_db()

# ==========================================
# 💬 채팅 로직
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# 헤더 출력
st.markdown("<div class='enterprise-header'><h1>🏅 인증조사 마스터 AI (초고속 RAG 버전)</h1></div>", unsafe_allow_html=True)

# 채팅 내역 표시 컨테이너
chat_container = st.container(height=500)
with chat_box := chat_container:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# 질문 입력
if prompt := st.chat_input("규정에 대해 무엇이든 물어보세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with chat_box:
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            # 1. 관련 조각 찾기 (600페이지 중 딱 4조각만!)
            docs = vdb.similarity_search(prompt, k=4)
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # 2. 좁혀진 범위로만 답변 생성
            final_prompt = f"""너는 검단탑병원의 '인증조사 마스터 AI'야. 
            아래 제공된 [지침서 조각] 내용만을 근거로 답변해줘. 
            만약 지침서에 없는 내용이라면 모른다고 대답하고, 아는 척 하지마.
            답변 끝에는 반드시 "[근거 내용: ...]"을 요약해서 달아줘.

            [지침서 조각]
            {context}

            질문: {prompt}
            """
            
            response_container = st.empty()
            full_response = ""
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            try:
                # 데이터가 매우 작으므로 과부하 없이 즉시 응답
                res = model.generate_content(final_prompt, stream=True)
                for chunk in res:
                    full_response += chunk.text
                    response_container.markdown(full_response + "▌")
                response_container.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"⚠️ 시스템 과부하 또는 오류 발생: {e}")
