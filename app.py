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

# ============================================================
# 🔐 1. 보안 설정 및 UI 스타일링 (디자인 핵심)
# ============================================================
SET_PASSWORD = "0366"  # 선생님이 정하신 보안 코드

st.set_page_config(
    page_title="검단탑병원 인증 AI", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# [UI 디자인] 검색창 파란 테두리 및 병원 전용 스타일
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    
    /* 상단 헤더 디자인 */
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
        margin: 0; font-size: 1.8rem; font-weight: 800; color: white; letter-spacing: -0.5px; 
    }
    
    /* [핵심 요청] 검색창 진한 파란색 테두리 강조 */
    [data-testid="stChatInput"] { 
        border: 3px solid #005691 !important; 
        border-radius: 12px !important; 
        box-shadow: 0 4px 15px rgba(0, 51, 145, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# [보안 로직]
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png")
        pwd = st.text_input("시스템 보안 코드를 입력하십시오.", type="password")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
    st.stop()

# ============================================================
# 🔑 2. 무적의 API 키 로테이션 및 모델 스위칭 엔진
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))

# 모든 키 형태를 리스트로 안전하게 파싱
if isinstance(raw_keys, str):
    API_KEYS = [k.strip() for k in raw_keys.replace("[", "").replace("]", "").replace('"', '').replace("'", "").split(",") if k.strip()]
else:
    API_KEYS = list(raw_keys)

if not API_KEYS:
    st.error("❌ 등록된 API 키가 없습니다. 관리자 설정을 확인하세요.")
    st.stop()

def generate_with_retry(prompt_text):
    """키 로테이션 + 모델 자동 우회(2.5 -> 1.5) 기능"""
    keys = list(API_KEYS)
    random.shuffle(keys) # 매번 순서를 섞어 한도 분산
    
    for key in keys:
        try:
            genai.configure(api_key=key)
            try:
                # [2.5-flash] 우선 시도
                model = genai.GenerativeModel('gemini-2.5-flash')
                return model.generate_content(prompt_text, stream=True)
            except Exception as e:
                # [1.5-flash] 404 등 에러 시 자동 우회
                model = genai.GenerativeModel('gemini-1.5-flash')
                return model.generate_content(prompt_text, stream=True)
        except ResourceExhausted:
            continue # 한도 초과 시 다음 키로
        except Exception:
            continue
            
    raise Exception("현재 모든 엔진의 사용량이 초back되었거나 연결이 원활하지 않습니다.")

# ============================================================
# 📚 3. 지능형 지식 DB 구축 (로딩 % 숫자 + 0초 로딩 기술)
# ============================================================
@st.cache_resource
def load_or_build_vdb():
    index_path = "faiss_index_saved"
    
    # [404 방어] 작동하는 임베딩 모델 찾기
    embeddings = None
    working_key = API_KEYS[0]
    
    # 최신 모델(text-embedding-004)부터 차례대로 시도
    for m_name in ["models/text-embedding-004", "models/embedding-001", "embedding-001"]:
        try:
            e = GoogleGenerativeAIEmbeddings(model=m_name, google_api_key=working_key)
            e.embed_query("test")
            embeddings = e
            break
        except: pass

    if not embeddings:
        return None, "❌ 구글 서버 연결 실패. API 권한 설정을 확인하십시오."

    # [0초 로딩] 이미 저장된 데이터가 있으면 즉시 로드 (선생님 요청 사항)
    if os.path.exists(index_path):
        try:
            return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True), None
        except: pass 

    # [신규 분석] PDF 지침서 읽기 시작
    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files: return None, "🚨 서버에 지침서 파일이 없습니다."

    # 전체 페이지 계산 (퍼센트 수치용)
    total_pages = 0
    for f in valid_files:
        try: total_pages += len(PdfReader(f).pages)
        except: pass
            
    p_bar = st.progress(0)
    s_text = st.empty()
    all_text = ""
    current_page = 0
    
    # [1단계] 텍스트 추출 (1% ~ 40%)
    for f in valid_files:
        reader = PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t: all_text += t
            current_page += 1
            # 실시간 퍼센트 및 페이지 수 표시 (선생님 요청)
            p_val = int((current_page / total_pages) * 40)
            p_bar.progress(p_val / 100.0)
            s_text.markdown(f"📡 **[1/2] 지침서 분석 중: {p_val}% 완료** ({current_page}/{total_pages}장 읽음)")
            
    try:
        # 텍스트 쪼개기
        splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
        chunks = splitter.split_text(all_text)
        vector_db = None
        total_chunks = len(chunks)
        
        # [2단계] 지식 구조화 (41% ~ 100% / 안전 휴식 포함)
        for i in range(0, total_chunks, 100):
            batch = chunks[i:i+100]
            if vector_db is None:
                vector_db = FAISS.from_texts(batch, embeddings)
            else:
                vector_db.add_texts(batch)
            
            c_val = 40 + int(((min(i + 100, total_chunks)) / total_chunks) * 60)
            p_bar.progress(c_val / 100.0)
            s_text.markdown(f"🧠 **[2/2] 지능화 최적화 중: {c_val}% 완료** (시스템 보호 모드)")
            time.sleep(1.5) # 과부하 방어 (1.5초 휴식)
            
        vector_db.save_local(index_path) # 영구 저장
        p_bar.empty(); s_text.empty()
        return vector_db, None
    except Exception as e:
        return None, f"❌ 오류 발생: {e}"

# 엔진 기동
vdb_obj, error_msg = load_or_build_vdb()

# 상단 헤더 렌더링
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
    st.success(f"📡 **시스템 상태:** 정상 구동 중")
    st.info(f"🔑 **가동 엔진:** {len(API_KEYS)}개")
    if st.button("🔄 시스템 메모리 정리", use_container_width=True):
        st.session_state.clear(); st.rerun()

if error_msg: st.error(error_msg); st.stop()
vdb = vdb_obj

# ============================================================
# 🗂️ 4. 메인 기능 탭 (검색 및 채점 훈련 완벽 탑재)
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

# --- TAB 1: 통합 규정 검색 (스트리밍 답변) ---
with tab1:
    chat_box1 = st.container(height=500)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if p := st.chat_input("인증 규정이나 지침을 입력하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": p})
        with chat_box1.chat_message("user"): st.markdown(p)
        
        with chat_box1.chat_message("assistant"):
            try:
                # 관련 근거 4개 찾기
                docs = vdb.similarity_search(p, k=4)
                ctx = "\n\n".join([d.page_content for d in docs])
                prompt = f"지침서 내용:\n{ctx}\n질문: {p}\n(한국어로 친절히 답하고 반드시 지침서상의 근거를 제시해줘)"
                
                # [핵심 요청] 타이핑 치듯 스트리밍 출력
                res_stream = generate_with_retry(prompt)
                full_res = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except: st.error("⚠️ 잠시 후 다시 질문해 주세요.")

# --- TAB 2: AI 감독관 훈련 (채점 및 피드백 기능) ---
with tab2:
    st.info("💡 아래 버튼을 눌러 실제 감독관의 질문에 답변해 보세요.")
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    # 감독관 질문 생성 버튼
    if st.button("▶️ 새로운 감독관 현장 질문 받기", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            try:
                # 질문 생성 및 스트리밍 출력
                q_prompt = "병원 인증평가 감독관처럼 간호사나 직원에게 던질법한 짧고 날카로운 현장 질문 하나만 한국어로 해줘."
                res_stream = generate_with_retry(q_prompt)
                full_q = st.write_stream(res_stream)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
            except: st.error("⚠️ 질문 생성 실패")

    # 답변 입력 및 AI 실시간 채점
    if train_p := st.chat_input("감독관의 질문에 답변하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": train_p})
            with chat_box2.chat_message("user"): st.markdown(train_p)
            
            with chat_box2.chat_message("assistant"):
                try:
                    # 지침서에서 정답 근거 찾기
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    ctx = "\n\n".join([d.page_content for d in docs])
                    
                    eval_p = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{train_p}'\n[지침서 근거]\n{ctx}\n\n위 지침서를 바탕으로 답변이 맞는지 평가하고, 부족하다면 정답을 알려줘."
                    
                    # [핵심 요청] 채점 결과도 스트리밍 출력
                    res_eval = generate_with_retry(eval_p)
                    full_eval = st.write_stream(res_eval)
                    
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_eval})
                    st.session_state.current_q = None # 답변 완료 후 질문 초기화
                except: st.error("⚠️ 채점 엔진 지연")
        else:
            st.warning("먼저 위쪽의 '질문 받기' 버튼을 눌러주세요.")
