import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
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
st.set_page_config(page_title="검단탑병원 인증 AI", page_icon="🏅", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 20px 30px; border-radius: 12px; margin-bottom: 25px;
    }
    .badge { background: #8CC63F; color: #003366; padding: 4px 10px; border-radius: 4px; font-weight: bold; margin-bottom:5px; display:inline-block;}
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; font-weight: 800; color: white; letter-spacing: -0.5px; }
    /* 검색창 파란색 테두리 */
    [data-testid="stChatInput"] { border: 2px solid #005691 !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("authenticated", False):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
        pwd = st.text_input("보안 코드를 입력하십시오.", type="password")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# ==========================================
# 🔑 2. 무적의 시크릿 키 파싱 & 로테이션 엔진
# ==========================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
if isinstance(raw_keys, str):
    API_KEYS = [k.strip() for k in raw_keys.replace("[", "").replace("]", "").replace('"', '').replace("'", "").split(",") if k.strip()]
else:
    API_KEYS = list(raw_keys)

if not API_KEYS:
    st.error("❌ 구글 API 키가 설정되지 않았습니다.")
    st.stop()

def generate_with_retry(prompt_text):
    """키 로테이션 + 2.5/1.5 자동 스위칭"""
    keys = list(API_KEYS)
    random.shuffle(keys)
    
    last_error = None
    for key in keys:
        try:
            genai.configure(api_key=key)
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                return model.generate_content(prompt_text, stream=True)
            except Exception as inner_e:
                if "404" in str(inner_e) or "not found" in str(inner_e).lower():
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    return model.generate_content(prompt_text, stream=True)
                raise inner_e
        except ResourceExhausted:
            continue
        except Exception as e:
            last_error = e
            continue
            
    raise Exception("현재 등록된 모든 API 키의 한도가 초과되었거나 응답이 없습니다.")

# ==========================================
# 📚 3. 지식 DB 영구 캐싱 (로딩 0초 기술)
# ==========================================
@st.cache_resource
def load_or_build_vdb():
    index_path = "faiss_index_saved"
    working_key = random.choice(API_KEYS)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=working_key)

    if os.path.exists(index_path):
        try:
            return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        except: pass 

    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files: return None

    progress_bar = st.progress(0)
    status_text = st.empty()
    all_text = ""
    
    for idx, f in enumerate(valid_files):
        try:
            reader = PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t: all_text += t
        except: continue
        progress_bar.progress((idx + 1) / len(valid_files) * 0.4)
        status_text.markdown("📡 **지침서 텍스트 추출 중...**")
            
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
        chunks = text_splitter.split_text(all_text)
        
        vector_db = FAISS.from_texts(chunks[:100], embeddings)
        for i in range(100, len(chunks), 100):
            vector_db.add_texts(chunks[i:i+100])
            progress_bar.progress(0.4 + (i / len(chunks)) * 0.6)
            status_text.markdown(f"🧠 **구조화 중 (과부하 방지 안전 모드)...**")
            time.sleep(1.5)
            
        vector_db.save_local(index_path)
        progress_bar.empty()
        status_text.empty()
        return vector_db
    except Exception as e:
        status_text.empty()
        progress_bar.empty()
        return "QUOTA_ERROR" if "quota" in str(e).lower() else None

vdb = load_or_build_vdb()

# 상단 헤더
st.markdown("<div class='enterprise-header'><div><div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div><h1>🏅 인증조사 마스터 AI</h1></div></div>", unsafe_allow_html=True)

with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.info(f"📡 **시스템 상태:** 최적화 완료\n\n🔑 가동 중인 AI 엔진: {len(API_KEYS)}개")
    if st.button("🔄 시스템 메모리 정리", use_container_width=True):
        st.session_state.clear()
        st.rerun()

if vdb == "QUOTA_ERROR":
    st.error("⚠️ 지식 DB 구축을 위한 API 사용량이 부족합니다.")
    st.stop()
elif vdb is None:
    st.error("⚠️ 지침서 파일을 찾을 수 없거나 텍스트를 읽을 수 없습니다.")
    st.stop()

# ==========================================
# 🗂️ 4. 메인 탭 로직 (누락 기능 완전 복구)
# ==========================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

# --- TAB 1: 규정 검색 ---
with tab1:
    chat_box1 = st.container(height=450)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("규정이나 지침을 입력하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": p})
        with chat_box1.chat_message("user"): st.markdown(p)
        with chat_box1.chat_message("assistant"):
            try:
                docs = vdb.similarity_search(p, k=4)
                context = "\n\n".join([d.page_content for d in docs])
                prompt = f"지침서 내용:\n{context}\n질문: {p}\n(한국어로 친절히 답하고 근거를 제시해줘)"
                
                res_stream = generate_with_retry(prompt)
                full_res = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except Exception as e:
                st.error("⚠️ 현재 시스템 응답이 지연되고 있습니다. 잠시 후 시도해 주세요.")

# --- TAB 2: 감독관 훈련 (삭제됐던 채점 기능 완벽 복원) ---
with tab2:
    st.info("💡 실전 대응 능력을 키우기 위해 감독관의 질문에 답변해 보세요.")
    
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    if st.button("▶️ 새로운 감독관 질문 받기", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            try:
                res_stream = generate_with_retry("인증평가 감독관처럼 짧고 핵심적인 질문 하나만 한국어로 해줘. 다른 말은 하지마.")
                full_q = st.write_stream(res_stream)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
            except Exception as e:
                st.error("⚠️ 질문을 생성할 수 없습니다. 엔진 사용량이 초과되었을 수 있습니다.")
                st.session_state.current_q = None

    # 🔥 실수로 통째로 날려먹었던 바로 그 입력창/채점 기능!
    if train_prompt := st.chat_input("감독관의 질문에 답변하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": train_prompt})
            with chat_box2.chat_message("user"): st.markdown(train_prompt)
            with chat_box2.chat_message("assistant"):
                try:
                    # 지침서 뒤져서 정확하게 채점하기
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    context = "\n\n".join([doc.page_content for doc in docs])
                    eval_prompt = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{train_prompt}'\n[지침서 근거]\n{context}\n\n위 지침서를 바탕으로 답변이 맞는지 짧게 평가해주고 정답을 알려줘."
                    
                    res_eval_stream = generate_with_retry(eval_prompt)
                    full_eval = st.write_stream(res_eval_stream)
                    
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_eval})
                    st.session_state.current_q = None # 답변했으니 초기화
                except Exception as e:
                    st.error("⚠️ 평가를 생성할 수 없습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.warning("먼저 위쪽의 '▶️ 새로운 감독관 질문 받기' 버튼을 눌러 질문을 받아주세요.")
