import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
# [오류 방어] 최신 라이브러리 호환성 유지
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import time
import random
from google.api_core.exceptions import ResourceExhausted

# ==========================================
# 🔐 1. 보안 및 UI 최적화 설정
# ==========================================
SET_PASSWORD = "0366"

st.set_page_config(
    page_title="검단탑병원 인증 AI", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# [디자인] 검색창 진한 파란색 테두리 및 병원 폰트 스타일 적용
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; 
        padding: 20px 30px; 
        border-radius: 12px; 
        margin-bottom: 25px;
    }
    .badge { 
        background: #8CC63F; 
        color: #003366; 
        padding: 4px 10px; 
        border-radius: 4px; 
        font-weight: bold; 
        margin-bottom: 5px; 
        display: inline-block;
    }
    .enterprise-header h1 { 
        margin: 0; 
        font-size: 1.8rem; 
        font-weight: 800; 
        color: white; 
        letter-spacing: -0.5px; 
    }
    /* [선생님 핵심 요청] 검색창 파란색 테두리 */
    [data-testid="stChatInput"] { 
        border: 2px solid #005691 !important; 
        border-radius: 12px !important; 
        box-shadow: 0 4px 12px rgba(0, 86, 145, 0.15) !important;
    }
</style>
""", unsafe_allow_html=True)

# [보안] 관리자 인증 로직
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png")
        pwd = st.text_input("보안 코드를 입력하십시오.", type="password")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# ==========================================
# 🔑 2. 다중 API 키 로테이션 엔진
# ==========================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))

# 모든 형태의 입력을 리스트로 정제
if isinstance(raw_keys, str):
    API_KEYS = [k.strip() for k in raw_keys.replace("[", "").replace("]", "").replace('"', '').replace("'", "").split(",") if k.strip()]
else:
    API_KEYS = list(raw_keys)

if not API_KEYS:
    st.error("❌ 구글 API 키가 설정되지 않았습니다.")
    st.stop()

# [무적 방어] 모델 스위칭 및 키 뺑뺑이 함수
def generate_with_retry(prompt_text):
    keys = list(API_KEYS)
    random.shuffle(keys) # 시도시마다 순서 섞기
    
    for key in keys:
        try:
            genai.configure(api_key=key)
            try:
                # 2.5 막히면 1.5로 자동 스위칭
                model = genai.GenerativeModel('gemini-2.5-flash')
                return model.generate_content(prompt_text, stream=True)
            except:
                model = genai.GenerativeModel('gemini-1.5-flash')
                return model.generate_content(prompt_text, stream=True)
        except ResourceExhausted: continue
        except: continue
            
    raise Exception("모든 API 엔진이 사용량 초과 상태입니다. 잠시 후 시도하세요.")

# ==========================================
# 📚 3. 지식 구조화 (로딩 % 숫자 + 0초 로딩)
# ==========================================
@st.cache_resource
def load_or_build_vdb():
    index_path = "faiss_index_saved"
    
    # 가동 가능한 임베딩 모델 탐색
    embeddings = None
    for key in API_KEYS:
        for m_name in ["models/text-embedding-004", "models/embedding-001"]:
            try:
                e = GoogleGenerativeAIEmbeddings(model=m_name, google_api_key=key)
                e.embed_query("test")
                embeddings = e
                break
            except: pass
        if embeddings: break

    if not embeddings: return None, "❌ 구글 서버 연결 실패 (키 권한 확인)"

    # [0초 로딩] 이미 저장된 데이터가 있으면 즉시 로드
    if os.path.exists(index_path):
        try:
            return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True), None
        except: pass 

    # 신규 분석 시작
    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files: return None, "🚨 서버에 PDF 파일이 없습니다."

    # 페이지 수 계산 (퍼센트 수치용)
    total_pages = 0
    for f in valid_files:
        try: total_pages += len(PdfReader(f).pages)
        except: pass
            
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_text = ""
    current_page = 0
    
    # 1단계: 텍스트 추출 (1% ~ 40%)
    for f in valid_files:
        reader = PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t: all_text += t
            current_page += 1
            p_val = int((current_page / total_pages) * 40)
            progress_bar.progress(p_val / 100.0)
            status_text.markdown(f"📡 **[1/2] 지침서 분석 중: {p_val}% 완료** ({current_page}/{total_pages}장)")
            
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
        chunks = text_splitter.split_text(all_text)
        vector_db = None
        total_chunks = len(chunks)
        
        # 2단계: 최적화 (41% ~ 100% / 안전 휴식 포함)
        for i in range(0, total_chunks, 100):
            batch = chunks[i:i+100]
            if vector_db is None: vector_db = FAISS.from_texts(batch, embeddings)
            else: vector_db.add_texts(batch)
            c_val = 40 + int(((min(i + 100, total_chunks)) / total_chunks) * 60)
            progress_bar.progress(c_val / 100.0)
            status_text.markdown(f"🧠 **[2/2] 지능화 중: {c_val}% 완료**")
            time.sleep(1.5) # 과부하 방어
            
        vector_db.save_local(index_path) # 영구 저장
        progress_bar.empty(); status_text.empty()
        return vector_db, None
    except Exception as e:
        return None, f"❌ 오류 발생: {e}"

vdb_obj, error_msg = load_or_build_vdb()

# 상단 UI 헤더
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
    st.info(f"📡 **시스템 상태:** 정상\n\n🔑 가동 엔진: {len(API_KEYS)}개")
    if st.button("🔄 시스템 메모리 정리", use_container_width=True):
        st.session_state.clear(); st.rerun()

if error_msg: st.error(error_msg); st.stop()
vdb = vdb_obj

# ==========================================
# 🗂️ 4. 메인 기능 (검색 및 채점 훈련)
# ==========================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

# --- TAB 1: 규정 검색 ---
with tab1:
    chat_box1 = st.container(height=500)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("규정이나 지침을 입력하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": p})
        with chat_box1.chat_message("user"): st.markdown(p)
        with chat_box1.chat_message("assistant"):
            try:
                docs = vdb.similarity_search(p, k=4)
                ctx = "\n\n".join([d.page_content for d in docs])
                prompt = f"지침서 내용:\n{ctx}\n질문: {p}\n(한국어로 친절히 답하고 근거를 제시해줘)"
                # 타이핑 스트리밍 출력
                res_stream = generate_with_retry(prompt)
                full_res = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except: st.error("⚠️ 잠시 후 다시 질문해 주세요.")

# --- TAB 2: 감독관 훈련 (채점 기능 완벽 포함) ---
with tab2:
    st.info("💡 버튼을 눌러 감독관의 질문에 답변해 보세요.")
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    if st.button("▶️ 새로운 감독관 현장 질문 받기", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            try:
                res_stream = generate_with_retry("인증평가 감독관처럼 짧은 현장 질문 하나만 한국어로 해줘.")
                full_q = st.write_stream(res_stream)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
            except: st.error("⚠️ 질문 생성 실패")

    if train_p := st.chat_input("감독관 질문에 답변하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": train_p})
            with chat_box2.chat_message("user"): st.markdown(train_p)
            with chat_box2.chat_message("assistant"):
                try:
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    ctx = "\n\n".join([d.page_content for d in docs])
                    eval_p = f"질문: '{st.session_state.current_q}'\n답변: '{train_p}'\n근거:\n{ctx}\n평가 및 정답 알려줘."
                    # 채점 결과 스트리밍 출력
                    res_eval = generate_with_retry(eval_p)
                    full_eval = st.write_stream(res_eval)
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_eval})
                    st.session_state.current_q = None 
                except: st.error("⚠️ 채점 실패")
        else: st.warning("먼저 질문을 받아주세요.")
