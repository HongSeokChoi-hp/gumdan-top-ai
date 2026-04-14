import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import time
import random

# ============================================================
# 🎨 1. [디자인/보안] 병원 전용 프리미엄 UI 및 테두리 설정
# ============================================================
SET_PASSWORD = "0366" 

st.set_page_config(
    page_title="검단탑병원 인증 AI 마스터", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 45px 55px; border-radius: 20px; margin-bottom: 45px;
        box-shadow: 0 15px 50px rgba(0, 51, 145, 0.35);
    }
    .badge { 
        background: #8CC63F; color: #003366; padding: 10px 20px; 
        border-radius: 8px; font-weight: bold; margin-bottom: 20px; display: inline-block;
        font-size: 1rem;
    }
    .enterprise-header h1 { 
        margin: 0; font-size: 3.2rem; font-weight: 900; color: white; letter-spacing: -2px; 
    }

    [data-testid="stChatInput"] { 
        border: 4px solid #005691 !important; 
        border-radius: 20px !important; 
        box-shadow: 0 15px 55px rgba(0, 86, 145, 0.4) !important;
        background-color: white !important;
        padding: 18px !important;
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    .stTabs [data-baseweb="tab"] {
        height: 75px; background-color: #f1f5f9; border-radius: 15px 15px 0 0; 
        padding: 0 50px; font-weight: 800; color: #64748b; font-size: 1.3rem;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #005691 !important; color: white !important; 
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png")
        st.markdown("<h2 style='text-align:center;'>🏥 검단탑병원 인증 AI 시스템</h2>", unsafe_allow_html=True)
        pwd = st.text_input("접속 코드를 입력하십시오.", type="password", placeholder="보안 코드를 입력하세요")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            if pwd: st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🔑 2. [엔진] 무적의 API 키 로테이션 엔진
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

if not API_KEYS:
    st.error("🚨 설정된 API 키가 없습니다.")
    st.stop()

def generate_with_retry(prompt_text):
    keys = list(API_KEYS)
    random.shuffle(keys)
    for key in keys:
        try:
            genai.configure(api_key=key)
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                return model.generate_content(prompt_text, stream=True)
            except:
                model = genai.GenerativeModel('gemini-1.5-flash')
                return model.generate_content(prompt_text, stream=True)
        except: continue
    raise Exception("모든 AI 엔진이 응답하지 않습니다.")

# ============================================================
# 📚 3. [지능화] 데이터 분석 (무한 로딩 버그 완벽 해결)
# ============================================================
@st.cache_resource
def load_or_build_vdb():
    working_key = API_KEYS[0]

    # 선생님 계정 전용 맞춤형 모델 탑재 완료!
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001", 
            google_api_key=working_key
        )
        embeddings.embed_query("connection_test")
    except Exception as e:
        try:
            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-2-preview", 
                google_api_key=working_key
            )
            embeddings.embed_query("connection_test")
        except Exception as e2:
            return None, f"지능형 모델 연결 실패: {str(e2)}"

    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files:
        return None, "🚨 서버에 분석할 지침서 파일(PDF)이 존재하지 않습니다."

    total_pages = 0
    for f in valid_files:
        try: total_pages += len(PdfReader(f).pages)
        except: pass
            
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_text = ""
    current_page = 0
    
    for f in valid_files:
        reader = PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t: all_text += t
            current_page += 1
            percent = int((current_page / total_pages) * 40)
            progress_bar.progress(percent / 100.0)
            status_text.markdown(f"📡 **지침서 데이터 분석 중: {percent}% 완료** (총 {total_pages}장 중 {current_page}장 분석)")
            
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=950, chunk_overlap=150)
        chunks = splitter.split_text(all_text)
        vector_db = None
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, 100):
            batch = chunks[i:i+100]
            if vector_db is None:
                vector_db = FAISS.from_texts(batch, embeddings)
            else:
                vector_db.add_texts(batch)
            
            c_percent = 40 + int(((min(i + 100, total_chunks)) / total_chunks) * 60)
            progress_bar.progress(c_percent / 100.0)
            status_text.markdown(f"🧠 **지식 최적화 구축 중: {c_percent}% 완료** (시스템 보호 모드)")
            time.sleep(1.6) 
            
        # [해결] 파일 저장 코드를 삭제하여 스트림릿 무한 재시작 방지 (메모리에만 상주)
        progress_bar.empty(); status_text.empty()
        return vector_db, None
    except Exception as e:
        return None, f"지식 구축 중 오류 발생: {str(e)}"

st.markdown("""
<div class='enterprise-header'>
    <div>
        <div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div>
        <h1>🏅 인증조사 마스터 AI</h1>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): 
        st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.success("📡 **시스템 상태: 정상 작동 중**")
    st.info(f"🔑 **활성 엔진:** {len(API_KEYS)}개")
    if st.button("🔄 지식 메모리 초기화", use_container_width=True):
        st.session_state.clear()
        st.rerun()

vdb, error_msg = load_or_build_vdb()
if error_msg: st.error(error_msg); st.stop()

# ============================================================
# 🗂️ 4. 메인 탭 기능 (검색 / 훈련)
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

with tab1:
    chat_box1 = st.container(height=520)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정이나 지침에 대해 질문하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with chat_box1.chat_message("user"): st.markdown(query)
        with chat_box1.chat_message("assistant"):
            try:
                docs = vdb.similarity_search(query, k=4)
                context_data = "\n\n".join([d.page_content for d in docs])
                full_prompt = f"지침서 내용:\n{context_data}\n\n질문: {query}\n(한국어로 친절하게 답변하고 지침서에 기반한 근거를 반드시 포함해줘.)"
                stream_res = generate_with_retry(full_prompt)
                full_res = st.write_stream(stream_res)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except: st.error("⚠️ 시스템 지연입니다. 잠시 후 시도해주세요.")

with tab2:
    st.info("💡 현장 감독관의 질문에 답변하여 실전 능력을 테스트하십시오.")
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    if st.button("▶️ 새로운 감독관 현장 질문 생성", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            try:
                stream_q = generate_with_retry("병원 인증평가 감독관이 직원에게 던질법한 짧은 현장 질문 하나만 한국어로 해줘.")
                full_q = st.write_stream(stream_q)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
            except: st.error("⚠️ 질문 생성 실패.")

    if answer_input := st.chat_input("감독관의 질문에 답변을 입력하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": answer_input})
            with chat_box2.chat_message("user"): st.markdown(answer_input)
            with chat_box2.chat_message("assistant"):
                try:
                    search_docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    ref_context = "\n\n".join([d.page_content for d in search_docs])
                    eval_p = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{answer_input}'\n지침서:\n{ref_context}\n\n위 내용을 바탕으로 채점하고 정답을 알려줘."
                    eval_stream = generate_with_retry(eval_p)
                    final_eval = st.write_stream(eval_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": final_eval})
                    st.session_state.current_q = None 
                except: st.error("⚠️ 채점 엔진 오류.")
        else: st.warning("먼저 질문 생성 버튼을 눌러주십시오.")
