import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
import os
import time
import random
import requests
import json

# ============================================================
# 🎨 1. [디자인/보안] 병원 전용 프리미엄 UI 및 테두리 설정 (기능 1~4)
# ============================================================
SET_PASSWORD = "0366" # [기능 1] 보안 코드

st.set_page_config(
    page_title="검단탑병원 인증 AI 마스터", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# [기능 2] 검색창 진한 파란색 4px 테두리 (#005691) 적용
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 40px 55px; border-radius: 20px; margin-bottom: 45px;
        box-shadow: 0 15px 50px rgba(0, 51, 145, 0.35);
    }
    .badge { 
        background: #8CC63F; color: #003366; padding: 8px 18px; 
        border-radius: 8px; font-weight: bold; margin-bottom: 18px; display: inline-block;
    }
    .enterprise-header h1 { margin: 0; font-size: 3rem; font-weight: 900; letter-spacing: -2px; }

    /* [기능 2] 검색창 진한 파란색 4px 테두리 및 프리미엄 효과 */
    [data-testid="stChatInput"] { 
        border: 4px solid #005691 !important; 
        border-radius: 20px !important; 
        box-shadow: 0 15px 50px rgba(0, 86, 145, 0.45) !important;
        background-color: white !important;
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    .stTabs [data-baseweb="tab"] {
        height: 75px; background-color: #f1f5f9; border-radius: 15px 15px 0 0; 
        padding: 0 50px; font-weight: 800; color: #64748b; font-size: 1.25rem;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #005691 !important; color: white !important; 
    }
</style>
""", unsafe_allow_html=True)

# [기능 1] 보안 코드 인증
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
        st.markdown("<h2 style='text-align:center;'>🏥 검단탑병원 인증 AI 시스템</h2>", unsafe_allow_html=True)
        pwd = st.text_input("접속 코드를 입력하십시오.", type="password", placeholder="보안 코드를 입력하세요")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            if pwd: st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🔑 2. [엔진] 404 박멸용 정식 v1 주소 직결 엔진 (기능 5, 6, 7)
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

# [기능 7] 모든 라이브러리를 무시하고 구글 서버 v1 주소로 직접 POST를 날리는 클래스
class UltimateV1Embeddings:
    def __init__(self, api_key):
        self.api_key = api_key
        # 라이브러리가 조작할 수 없는 "진짜 정식 주소"
        self.url = "https://generativelanguage.googleapis.com/v1/models/text-embedding-004:embedContent"

    def _get_embedding(self, text, task_type):
        headers = {'Content-Type': 'application/json'}
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type
        }
        # 꼼수 없이 정식 주소로 직접 찌릅니다.
        response = requests.post(f"{self.url}?key={self.api_key}", headers=headers, json=payload)
        if response.status_code != 200:
            raise Exception(f"구글 서버 거부 (상세: {response.text})")
        return response.json()['embedding']['values']

    def embed_documents(self, texts):
        return [self._get_embedding(t, "RETRIEVAL_DOCUMENT") for t in texts]
    
    def embed_query(self, text):
        return self._get_embedding(text, "RETRIEVAL_QUERY")

def generate_with_retry(prompt_text):
    """[기능 12, 15] 실시간 타이핑 출력 답변 엔진"""
    keys = list(API_KEYS)
    random.shuffle(keys)
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            return model.generate_content(prompt_text, stream=True)
        except: continue
    raise Exception("모든 AI 엔진이 응답하지 않습니다.")

# ============================================================
# 📚 3. [지능화] 데이터 분석 및 0초 로딩 (기능 8, 9, 10)
# ============================================================
@st.cache_resource
def load_or_build_vdb():
    index_path = "faiss_index_saved"
    working_key = API_KEYS[0]

    # [기능 7] 직결 엔진 가동
    try:
        embeddings = UltimateV1Embeddings(working_key)
        embeddings.embed_query("test") # 연결 테스트
    except Exception as e:
        return None, f"❌ 구글 정식 서버(v1) 연결 실패.\n상세 원인: {str(e)}"

    # [기능 8] 0초 로딩 (캐싱)
    if os.path.exists(index_path):
        try: return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True), None
        except: pass 

    # [기능 4] 용어 순화
    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files: return None, "🚨 서버에 지침서 파일(PDF)이 없습니다."

    # [기능 9] 진행률 계산
    total_pages = 0
    for f in valid_files:
        try: total_pages += len(PdfReader(f).pages)
        except: pass
            
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_text = ""
    current_page = 0
    
    # 📡 [기능 9] 1단계: 분석 (1% ~ 40%)
    for f in valid_files:
        reader = PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t: all_text += t
            current_page += 1
            percent = int((current_page / total_pages) * 40)
            progress_bar.progress(percent / 100.0)
            status_text.markdown(f"📡 **인증 지침서 데이터 분석 중: {percent}% 완료** ({current_page}/{total_pages}장)")
            
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=950, chunk_overlap=150)
        chunks = splitter.split_text(all_text)
        vector_db = None
        total_chunks = len(chunks)
        
        # 🧠 [기능 9, 10] 2단계: 구조화 (41% ~ 100%)
        for i in range(0, total_chunks, 100):
            batch = chunks[i:i+100]
            if vector_db is None: vector_db = FAISS.from_texts(batch, embeddings)
            else: vector_db.add_texts(batch)
            c_percent = 40 + int(((min(i + 100, total_chunks)) / total_chunks) * 60)
            progress_bar.progress(c_percent / 100.0)
            status_text.markdown(f"🧠 **지식 최적화 구축 중: {c_percent}% 완료**")
            time.sleep(1.6) # [기능 10] 시스템 보호
            
        vector_db.save_local(index_path)
        progress_bar.empty(); status_text.empty()
        return vector_db, None
    except Exception as e:
        return None, f"❌ 지식 구축 오류: {str(e)}"

# [기능 3, 4] 헤더
st.markdown("""
<div class='enterprise-header'>
    <div>
        <div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div>
        <h1>🏅 인증조사 마스터 AI</h1>
    </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.success("📡 **시스템 가동 중**")
    if st.button("🔄 시스템 초기화", use_container_width=True):
        st.session_state.clear(); st.rerun()

vdb, error_msg = load_or_build_vdb()
if error_msg: st.error(error_msg); st.stop()

# ============================================================
# 🗂️ 4. [기능 11~15] 규정 검색 및 AI 감독관 훈련
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

# --- TAB 1: [기능 11, 12] 검색 ---
with tab1:
    chat_box1 = st.container(height=520)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정이나 지침에 대해 질문하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with chat_box1.chat_message("user"): st.markdown(query)
        with chat_box1.chat_message("assistant"):
            try:
                # [기능 11] 근거 탐색
                docs = vdb.similarity_search(query, k=4)
                context_data = "\n\n".join([d.page_content for d in docs])
                full_prompt = f"지침서 내용:\n{context_data}\n\n질문: {query}\n(한국어로 친절하게 답변하고 근거를 반드시 포함해줘.)"
                # [기능 12] 스트리밍
                stream_res = generate_with_retry(full_prompt)
                full_res = st.write_stream(stream_res)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except Exception: st.error("⚠️ 시스템 지연 중")

# --- TAB 2: [기능 13, 14, 15] 훈련 ---
with tab2:
    st.info("💡 감독관의 질문에 답변하여 실전 능력을 테스트하십시오.")
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            try:
                stream_q = generate_with_retry("병원 인증평가 감독관처럼 짧은 현장 질문 하나만 한국어로 해줘.")
                full_q = st.write_stream(stream_q)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
            except Exception: st.error("⚠️ 질문 생성 실패")

    if answer_input := st.chat_input("감독관의 질문에 답변을 입력하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": answer_input})
            with chat_box2.chat_message("user"): st.markdown(answer_input)
            with chat_box2.chat_message("assistant"):
                try:
                    search_docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    ref_context = "\n\n".join([d.page_content for d in search_docs])
                    eval_prompt = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{answer_input}'\n지침서:\n{ref_context}\n\n위 내용을 바탕으로 채점하고 정답을 알려줘."
                    stream_eval = generate_with_retry(eval_prompt)
                    final_eval = st.write_stream(stream_eval)
                    st.session_state.train_msgs.append({"role": "assistant", "content": final_eval})
                    st.session_state.current_q = None 
                except Exception: st.error("⚠️ 채점 오류")
