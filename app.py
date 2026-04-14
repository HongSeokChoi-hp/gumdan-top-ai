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

# CSS: 카카오톡 스타일 UI
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

# 비밀번호 체크 로직
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

# API 키 설정
API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# ==========================================
# 📚 RAG 엔진: PDF 인덱싱 (에러 수정 버전)
# ==========================================
@st.cache_resource
def build_vector_db():
    all_text = ""
    pdf_files = ["guide.pdf", "manual2.pdf"]
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.write("📡 시스템 가동 중: 600페이지 지침서를 분석하고 있습니다. (약 30초 소요)")
    
    try:
        for idx, file in enumerate(pdf_files):
            if os.path.exists(file):
                reader = PdfReader(file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text: all_text += text
            progress_bar.progress((idx + 1) / len(pdf_files))
        
        # 텍스트 조각내기
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
        chunks = text_splitter.split_text(all_text)
        
        # 벡터 DB 생성
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
        vector_db = FAISS.from_texts(chunks, embeddings)
        
        progress_bar.empty()
        status_text.empty()
        return vector_db
    except Exception as e:
        st.error(f"❌ 인덱싱 중 오류 발생: {e}")
        return None

# 엔진 가동
vdb = build_vector_db()

# ==========================================
# 💬 채팅 인터페이스
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# 헤더
st.markdown("<div class='enterprise-header'><h1>🏅 인증조사 마스터 AI (RAG 엔진 가동)</h1></div>", unsafe_allow_html=True)

# 채팅 컨테이너 고정
chat_container = st.container(height=500)

# 채팅 내역 표시
with chat_container:
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# 질문 입력창 (에러 수정 포인트)
if prompt := st.chat_input("지침서에 대해 궁금한 점을 물어보세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 사용자 메시지 즉시 표시
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 답변 생성
        with st.chat_message("assistant"):
            if vdb is not None:
                # 1. 관련 내용 검색
                docs = vdb.similarity_search(prompt, k=4)
                context = "\n\n".join([doc.page_content for doc in docs])
                
                # 2. 프롬프트 구성
                final_prompt = f"""너는 검단탑병원의 '인증조사 마스터 AI'야. 
                아래 제공된 [지침서 내용]만을 근거로 친절하고 정확하게 답변해줘. 
                내용이 지침서에 없다면 모른다고 솔직하게 말해.
                
                [지침서 내용]
                {context}
                
                질문: {prompt}
                """
                
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(final_prompt, stream=True)
                    for chunk in res:
                        full_response += chunk.text
                        response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                except Exception as e:
                    st.error(f"⚠️ 답변 생성 중 오류: {e}")
            else:
                st.error("❌ 지식 베이스가 로드되지 않았습니다.")
