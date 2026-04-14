import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

# ==========================================
# 🔐 보안 및 초기 UI 설정
# ==========================================
SET_PASSWORD = "0366"
st.set_page_config(page_title="검단탑병원 인증 AI", page_icon="🏅", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 20px 30px; border-radius: 12px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 10px 20px rgba(0, 51, 102, 0.15);
        margin-bottom: 25px; border-left: 5px solid #8CC63F;
    }
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; font-weight: 800; color: white; letter-spacing: -0.5px; }
    .badge { background: #8CC63F; color: #003366; padding: 4px 10px; border-radius: 4px; font-weight: bold; margin-bottom:5px; display:inline-block;}
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: white; padding: 10px 20px 0px 20px; border-radius: 10px 10px 0 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"] { height: 50px; font-size: 1.05rem; font-weight: 600; color: #555; }
    .stTabs [aria-selected="true"] { color: #005691 !important; border-bottom-color: #005691 !important; border-bottom-width: 3px !important; }
    .stChatMessage { border-radius: 10px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;}
</style>
""", unsafe_allow_html=True)

# 인증 로직
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"):
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; margin:20px 0; font-weight:700;'>인증조사 마스터 AI 통합 시스템</h3>", unsafe_allow_html=True)
        pwd = st.text_input("보안 접근 코드를 입력하십시오.", type="password")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# ==========================================
# 🗂️ 왼쪽 사이드바 (부활!)
# ==========================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"):
        st.image("검단탑병원-로고_고화질.png", use_container_width=True)
    st.markdown("---")
    st.markdown("<div style='background:#f4f6f9; padding:15px; border-radius:8px; border:1px solid #e1e4e8;'>", unsafe_allow_html=True)
    st.markdown("🔒 **접속 등급:** 관리자 (1급)<br>📡 **서버 상태:** 최적화 (RAG 엔진)<br>📚 **지식 DB:**<br>• 2024 통합 지침서<br>• 급성기병원 표준지침서 Ver 5.0", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔄 시스템 메모리 정리", use_container_width=True):
        st.session_state.clear()
        st.rerun()

API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# ==========================================
# 📚 초고속 RAG 엔진 가동 (구글 에러 해결 버전)
# ==========================================
@st.cache_resource
def build_vector_db():
    all_text = ""
    pdf_files = ["guide.pdf", "manual2.pdf"]
    
    total_pages = 0
    valid_files = []
    for f in pdf_files:
        if os.path.exists(f):
            reader = PdfReader(f)
            total_pages += len(reader.pages)
            valid_files.append(f)
            
    if total_pages == 0: return None

    progress_bar = st.progress(0)
    status_text = st.empty()
    current_page = 0
    
    for file in valid_files:
        reader = PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if text: all_text += text
            current_page += 1
            percent = int((current_page / total_pages) * 100)
            progress_bar.progress(current_page / total_pages)
            status_text.markdown(f"📡 **지침서 분석 및 데이터 압축 중: {percent}% 완료**")
            
    status_text.markdown("🧠 **엔진 세팅 중... (약 10초)**")
    
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
        chunks = text_splitter.split_text(all_text)
        
        # [수정됨] 구글의 최신 임베딩 모델 이름으로 변경 (에러 해결 핵심)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=API_KEY)
        vector_db = FAISS.from_texts(chunks, embeddings)
        
        progress_bar.empty()
        status_text.empty()
        return vector_db
    except Exception as e:
        st.error(f"❌ 데이터 구조화 중 오류: {e}")
        return None

vdb = build_vector_db()

# 상단 헤더
st.markdown("""
<div class='enterprise-header'>
    <div>
        <div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div>
        <h1>🏅 인증조사 마스터 AI</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# 상태 저장소
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# ==========================================
# 🗂️ 탭 메뉴 (부활!)
# ==========================================
tab1, tab2 = st.tabs(["🔍 초고속 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

# --- TAB 1: 규정 검색 ---
with tab1:
    chat_box1 = st.container(height=450)
    with chat_box1:
        for m in st.session_state.search_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("검색할 규정이나 지침을 입력하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": prompt})
        with chat_box1:
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                if vdb is not None:
                    docs = vdb.similarity_search(prompt, k=4)
                    context = "\n\n".join([doc.page_content for doc in docs])
                    
                    final_prompt = f"너는 검단탑병원의 AI야. 아래 [지침서 내용]만을 근거로 한국어로 답해. 지침서에 없으면 모른다고 해.\n[지침서 내용]\n{context}\n질문: {prompt}"
                    
                    res_box = st.empty()
                    full_res = ""
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(final_prompt, stream=True)
                    for chunk in res:
                        full_res += chunk.text
                        res_box.markdown(full_res + "▌")
                    res_box.markdown(full_res)
                    st.session_state.search_msgs.append({"role": "assistant", "content": full_res})

# --- TAB 2: 감독관 훈련 ---
with tab2:
    chat_box2 = st.container(height=450)
    with chat_box2:
        for m in st.session_state.train_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])
            
        if st.session_state.current_q is None:
            with st.chat_message("assistant"):
                q_box = st.empty()
                model = genai.GenerativeModel('gemini-1.5-flash')
                res_q = model.generate_content("병원 인증평가 현장에서 직원에게 물어볼 아주 짧고 핵심적인 질문 1개만 한국어로 해줘.", stream=True)
                full_q = ""
                for chunk in res_q:
                    full_q += chunk.text
                    q_box.markdown(full_q + "▌")
                q_box.markdown(full_q)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})

    if train_prompt := st.chat_input("감독관의 질문에 답변하십시오...", key="train_input"):
        st.session_state.train_msgs.append({"role": "user", "content": train_prompt})
        with chat_box2:
            with st.chat_message("user"): st.markdown(train_prompt)
            with st.chat_message("assistant"):
                eval_box = st.empty()
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # RAG 엔진으로 정확하게 채점!
                if vdb is not None:
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    context = "\n\n".join([doc.page_content for doc in docs])
                    eval_prompt = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{train_prompt}'\n[지침서 근거]\n{context}\n\n위 지침서를 바탕으로 답변을 평가해주고, 다음 질문 1개를 이어서 내줘. 한국어로 해."
                else:
                    eval_prompt = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{train_prompt}'\n답변을 평가하고 다음 질문 1개만 해줘."

                res_eval = model.generate_content(eval_prompt, stream=True)
                full_eval = ""
                for chunk in res_eval:
                    full_eval += chunk.text
                    eval_box.markdown(full_eval + "▌")
                eval_box.markdown(full_eval)
                
                st.session_state.train_msgs.append({"role": "assistant", "content": full_eval})
                # 임시로 다음 질문을 세션에 통째로 저장 (로직 단순화)
                st.session_state.current_q = "다음 질문을 해주세요."
