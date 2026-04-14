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
SET_PASSWORD = "0366" 

st.set_page_config(
    page_title="검단탑병원 인증 AI 마스터", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# [기능 2] 검색창 진한 파란색 4px 테두리 적용
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

    /* [기능 2] 검색창 진한 파란색 4px 테두리 */
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
    .stTabs [aria-selected="true"] { background-color: #005691 !important; color: white !important; }
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
    st.stop()

# ============================================================
# 🔑 2. [엔진] 자가 치유형 5중 결합 직결 엔진 (기능 5, 6, 7)
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

class SelfHealingV1Embeddings:
    """[기능 7] 작동하는 주소를 찾을 때까지 스스로 열쇠를 깎는 엔진"""
    def __init__(self, api_key):
        self.api_key = api_key
        self.working_config = None
        # 시도할 수 있는 모든 주소와 모델명 조합
        self.configs = [
            {"version": "v1", "model": "models/text-embedding-004"},
            {"version": "v1", "model": "text-embedding-004"},
            {"version": "v1beta", "model": "models/text-embedding-004"},
            {"version": "v1", "model": "models/embedding-001"},
            {"version": "v1beta", "model": "models/embedding-001"}
        ]

    def _probe(self):
        for cfg in self.configs:
            try:
                url = f"https://generativelanguage.googleapis.com/{cfg['version']}/{cfg['model']}:embedContent?key={self.api_key}"
                payload = {"model": cfg['model'], "content": {"parts": [{"text": "test"}]}}
                res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload, timeout=5)
                if res.status_code == 200:
                    self.working_config = cfg
                    return True
            except: continue
        return False

    def embed_documents(self, texts):
        if not self.working_config: self._probe()
        results = []
        for t in texts:
            url = f"https://generativelanguage.googleapis.com/{self.working_config['version']}/{self.working_config['model']}:embedContent?key={self.api_key}"
            payload = {"model": self.working_config['model'], "content": {"parts": [{"text": t}]}}
            res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload).json()
            results.append(res['embedding']['values'])
        return results
    
    def embed_query(self, text):
        if not self.working_config: self._probe()
        url = f"https://generativelanguage.googleapis.com/{self.working_config['version']}/{self.working_config['model']}:embedContent?key={self.api_key}"
        payload = {"model": self.working_config['model'], "content": {"parts": [{"text": text}]}}
        res = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload).json()
        return res['embedding']['values']

def generate_with_retry(prompt_text):
    keys = list(API_KEYS); random.shuffle(keys)
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            return model.generate_content(prompt_text, stream=True)
        except: continue
    raise Exception("엔진 응답 없음")

# ============================================================
# 📚 3. [지능화] 데이터 분석 및 0초 로딩 (기능 8, 9, 10)
# ============================================================
@st.cache_resource
def load_or_build_vdb():
    index_path = "faiss_index_saved"
    working_key = API_KEYS[0]
    embeddings = SelfHealingV1Embeddings(working_key)

    if not embeddings._probe():
        return None, "❌ 모든 구글 서버 경로가 거부되었습니다. 결제 계정 연동을 확인하십시오."

    if os.path.exists(index_path):
        try: return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True), None
        except: pass 

    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files: return None, "🚨 지침서 파일(PDF)이 없습니다."

    total_pages = sum([len(PdfReader(f).pages) for f in valid_files])
    p_bar = st.progress(0); s_text = st.empty()
    all_text = ""; current_page = 0
    
    for f in valid_files:
        reader = PdfReader(f)
        for page in reader.pages:
            all_text += (page.extract_text() or "")
            current_page += 1
            percent = int((current_page / total_pages) * 40)
            p_bar.progress(percent / 100.0)
            s_text.markdown(f"📡 **데이터 분석 중: {percent}%** ({current_page}/{total_pages}장)")
            
    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=950, chunk_overlap=150)
        chunks = splitter.split_text(all_text)
        vector_db = None
        for i in range(0, len(chunks), 100):
            batch = chunks[i:i+100]
            if vector_db is None: vector_db = FAISS.from_texts(batch, embeddings)
            else: vector_db.add_texts(batch)
            c_p = 40 + int(((min(i + 100, len(chunks))) / len(chunks)) * 60)
            p_bar.progress(c_p / 100.0); s_text.markdown(f"🧠 **지식화 중: {c_p}%**")
            time.sleep(1.6)
            
        vector_db.save_local(index_path)
        p_bar.empty(); s_text.empty()
        return vector_db, None
    except Exception as e: return None, f"❌ 구축 오류: {str(e)}"

# [기능 3, 4] 헤더
st.markdown("<div class='enterprise-header'><div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div><h1>🏅 인증조사 마스터 AI</h1></div>", unsafe_allow_html=True)

with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.success("📡 시스템 정상 가동 중")
    if st.button("🔄 시스템 초기화", use_container_width=True):
        st.session_state.clear(); st.rerun()

vdb, error_msg = load_or_build_vdb()
if error_msg: st.error(error_msg); st.stop()

# ============================================================
# 🗂️ 4. [기능 11~15] 규정 검색 및 AI 훈련
# ============================================================
tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

with tab1:
    chat_box1 = st.container(height=520)
    if query := st.chat_input("규정에 대해 질문하십시오...", key="search_input"):
        with chat_box1.chat_message("user"): st.markdown(query)
        with chat_box1.chat_message("assistant"):
            docs = vdb.similarity_search(query, k=4)
            ctx = "\n\n".join([d.page_content for d in docs])
            full_prompt = f"내용:\n{ctx}\n질문: {query}\n(친절히 근거 포함 답변)"
            st.write_stream(generate_with_retry(full_prompt))

with tab2:
    st.info("💡 실전 대응 능력을 테스트하십시오.")
    chat_box2 = st.container(height=450)
    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        with chat_box2.chat_message("assistant"):
            st.write_stream(generate_with_retry("병원 인증평가 감독관처럼 짧은 현장 질문 하나 해줘."))
