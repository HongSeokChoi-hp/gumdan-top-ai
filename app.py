import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import time
from google.api_core.exceptions import ResourceExhausted

# ==========================================
# 🔐 보안 및 초기 UI 설정
# ==========================================
SET_PASSWORD = "0366"
st.set_page_config(page_title="검단탑병원 인증 AI", page_icon="🏅", layout="wide", initial_sidebar_state="expanded")

# 🔥 검색창 테두리 강조 및 깔끔한 UI 적용
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
    
    /* 검색창 파란색 테두리 적용 */
    [data-testid="stChatInput"] {
        border: 2px solid #005691 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    [data-testid="stChatInput"] textarea {
        font-size: 1.05rem !important;
    }
</style>
""", unsafe_allow_html=True)

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
# 🗂️ 왼쪽 사이드바
# ==========================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"):
        st.image("검단탑병원-로고_고화질.png", use_container_width=True)
    st.markdown("---")
    st.markdown("<div style='background:#f4f6f9; padding:15px; border-radius:8px; border:1px solid #e1e4e8;'>", unsafe_allow_html=True)
    st.markdown("🔒 **접속 등급:** 관리자 (1급)<br>📡 **서버 상태:** 정상 가동 중<br>📚 **지식 DB:**<br>• 2024 통합 지침서<br>• 급성기병원 표준지침서 Ver 5.0", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔄 시스템 메모리 정리", use_container_width=True):
        st.session_state.clear()
        st.rerun()

API_KEY = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=API_KEY)

# ==========================================
# 📚 지침서 분석 엔진 (404 & 과부하 원천 차단)
# ==========================================
@st.cache_resource
def build_vector_db():
    all_text = ""
    pdf_files = ["guide.pdf", "manual2.pdf"]
    total_pages = 0
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    
    for f in valid_files:
        reader = PdfReader(f)
        total_pages += len(reader.pages)
            
    if total_pages == 0: return None

    progress_bar = st.progress(0)
    status_text = st.empty()
    current_page = 0
    
    # 1단계: 텍스트 추출 (50% 진행)
    for file in valid_files:
        reader = PdfReader(file)
        for page in reader.pages:
            text = page.extract_text()
            if text: all_text += text
            current_page += 1
            percent = int((current_page / total_pages) * 50)
            progress_bar.progress(percent / 100.0)
            status_text.markdown(f"📡 **[1/2] 문서 분석 중: {percent}% 완료**")
            
    status_text.markdown("🧠 **[2/2] 시스템 지식 구조화 중... (안전 모드 가동, 약 15초 소요)**")
    
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
        chunks = text_splitter.split_text(all_text)
        
        # 🔥 404 에러 3중 방어막: 작동하는 모델 이름을 스스로 찾습니다.
        embeddings = None
        for model_name in ["models/embedding-001", "models/text-embedding-004", "embedding-001"]:
            try:
                temp_embeddings = GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=API_KEY)
                temp_embeddings.embed_query("test") # 찔러보기 테스트
                embeddings = temp_embeddings
                break # 성공하면 반복 중단
            except:
                continue # 실패하면 다음 모델 시도
                
        if embeddings is None:
            st.error("❌ 구글 서버가 현재 계정의 모든 임베딩 모델을 거부하고 있습니다.")
            return None

        # 🔥 과부하(429) 방어막: 데이터를 100개씩 쪼개서 넣고 2초씩 휴식합니다.
        batch_size = 100
        vector_db = None
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, batch_size):
            batch = chunks[i:i+batch_size]
            if vector_db is None:
                vector_db = FAISS.from_texts(batch, embeddings)
            else:
                vector_db.add_texts(batch)
            
            # 50% ~ 100% 진행률 계산
            current_chunk_percent = 50 + int(((min(i + batch_size, total_chunks)) / total_chunks) * 50)
            progress_bar.progress(current_chunk_percent / 100.0)
            status_text.markdown(f"🧠 **[2/2] 지식 구조화 중: {current_chunk_percent}% 완료** (구글 과부하 방지 중...)")
            
            time.sleep(2) # 2초 휴식 (핵심 안전장치)

        progress_bar.empty()
        status_text.empty()
        return vector_db
        
    except Exception as e:
        st.error(f"❌ 문서 처리 중 알 수 없는 오류 발생: {e}")
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

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# ==========================================
# 🗂️ 탭 메뉴 
# ==========================================
tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

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
                    try:
                        docs = vdb.similarity_search(prompt, k=4)
                        context = "\n\n".join([doc.page_content for doc in docs])
                        
                        final_prompt = f"너는 검단탑병원의 AI야. 아래 [지침서 내용]만을 근거로 한국어로 답해. 지침서에 없으면 모른다고 해.\n[지침서 내용]\n{context}\n질문: {prompt}"
                        
                        res_box = st.empty()
                        full_res = ""
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        res = model.generate_content(final_prompt, stream=True)
                        for chunk in res:
                            full_res += chunk.text
                            res_box.markdown(full_res + "▌")
                        res_box.markdown(full_res)
                        st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
                    except ResourceExhausted:
                        st.warning("⚠️ 잠시 접속량이 많습니다. 구글 서버 보호를 위해 약 30초 뒤에 다시 질문해 주세요.")
                    except Exception as e:
                        st.error(f"⚠️ 시스템 오류가 발생했습니다: {e}")

# --- TAB 2: 감독관 훈련 ---
with tab2:
    st.info("💡 감독관 훈련을 시작하려면 아래 버튼을 눌러주세요.")
    
    if st.button("▶️ 새로운 감독관 질문 받기", use_container_width=True):
        st.session_state.current_q = "생성중"
        
    chat_box2 = st.container(height=450)
    with chat_box2:
        for m in st.session_state.train_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])
            
        if st.session_state.current_q == "생성중":
            with st.chat_message("assistant"):
                try:
                    q_box = st.empty()
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    res_q = model.generate_content("병원 인증평가 현장에서 직원에게 물어볼 아주 짧고 핵심적인 질문 1개만 한국어로 해줘.", stream=True)
                    full_q = ""
                    for chunk in res_q:
                        full_q += chunk.text
                        q_box.markdown(full_q + "▌")
                    q_box.markdown(full_q)
                    st.session_state.current_q = full_q
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
                except ResourceExhausted:
                    st.warning("⚠️ 잠시 접속량이 많습니다. 30초 뒤에 다시 버튼을 눌러주세요.")
                    st.session_state.current_q = None

    if train_prompt := st.chat_input("감독관의 질문에 답변하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": train_prompt})
            with chat_box2:
                with st.chat_message("user"): st.markdown(train_prompt)
                with st.chat_message("assistant"):
                    try:
                        eval_box = st.empty()
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
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
                        st.session_state.current_q = None
                    except ResourceExhausted:
                        st.warning("⚠️ 잠시 접속량이 많습니다. 약 30초 뒤에 다시 시도해 주세요.")
        else:
            st.warning("먼저 위쪽의 '▶️ 새로운 감독관 질문 받기' 버튼을 눌러 질문을 받아주세요.")
