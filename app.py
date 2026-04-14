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
# 🔐 1. [디자인/보안] 병원 전용 UI 및 테두리 설정
# ============================================================
SET_PASSWORD = "0366" # 선생님 전용 보안코드

st.set_page_config(
    page_title="검단탑병원 인증 AI 마스터", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# [디자인 요구사항] 진한 파란색 테두리 및 프리텐다드 폰트 적용
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    
    /* 상단 엔터프라이즈 헤더 */
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 25px 35px; border-radius: 15px; margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .badge { 
        background: #8CC63F; color: #003366; padding: 5px 12px; 
        border-radius: 6px; font-weight: bold; margin-bottom: 8px; display: inline-block;
    }
    .enterprise-header h1 { margin: 0; font-size: 2rem; font-weight: 800; color: white; letter-spacing: -1px; }

    /* [선생님 핵심 요청] 검색창 진한 파란색 테두리 (#005691) */
    [data-testid="stChatInput"] { 
        border: 3px solid #005691 !important; 
        border-radius: 15px !important; 
        box-shadow: 0 4px 20px rgba(0, 86, 145, 0.2) !important;
        background-color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# [보안] 접속 비밀번호 확인
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png")
        st.subheader("🏥 시스템 보안 인증")
        pwd = st.text_input("접속 코드를 입력하십시오.", type="password", placeholder="****")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            if pwd: st.error("❌ 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🔑 2. [엔진] 무적의 API 키 로테이션 및 자동 모델 전환
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
if isinstance(raw_keys, str):
    API_KEYS = [k.strip() for k in raw_keys.replace("[", "").replace("]", "").replace('"', '').replace("'", "").split(",") if k.strip()]
else:
    API_KEYS = list(raw_keys)

if not API_KEYS:
    st.error("🚨 설정된 API 키가 없습니다. 관리자에게 문의하세요.")
    st.stop()

def generate_with_retry(prompt_text):
    """다중 키를 활용한 실시간 답변 생성 엔진 (스트리밍 지원)"""
    keys = list(API_KEYS)
    random.shuffle(keys)
    
    for key in keys:
        try:
            genai.configure(api_key=key)
            try:
                # 1순위: 최신 2.5 버전 시도
                model = genai.GenerativeModel('gemini-2.5-flash')
                return model.generate_content(prompt_text, stream=True)
            except Exception:
                # 2순위: 에러 시 1.5 버전으로 자동 하향 우회
                model = genai.GenerativeModel('gemini-1.5-flash')
                return model.generate_content(prompt_text, stream=True)
        except ResourceExhausted:
            continue
        except Exception:
            continue
    raise Exception("모든 엔진이 응답하지 않습니다. 키 권한이나 한도를 확인하세요.")

# ============================================================
# 📚 3. [지식] 지능형 데이터 분석 (실시간 퍼센트 + 0초 로딩)
# ============================================================
@st.cache_resource
def load_or_build_vdb():
    index_path = "faiss_index_saved"
    working_key = API_KEYS[0]

    # [범인 검거] 에러가 나면 뭉뚱그리지 않고 진짜 구글 메시지를 보여줍니다.
    embeddings = None
    last_raw_error = ""

    # 404 에러 방지를 위해 3가지 모델 이름을 순차적으로 찔러봅니다.
    for m_name in ["models/text-embedding-004", "models/embedding-001", "embedding-001"]:
        try:
            temp_emb = GoogleGenerativeAIEmbeddings(model=m_name, google_api_key=working_key)
            temp_emb.embed_query("test") 
            embeddings = temp_emb
            break
        except Exception as e:
            last_raw_error = str(e)
            continue

    if not embeddings:
        return None, f"❌ 구글 서버 연결 실패. (상세 에러: {last_raw_error})"

    # [0초 로딩] 이미 분석된 뇌가 있다면 즉시 로드 (선생님 핵심 요청)
    if os.path.exists(index_path):
        try:
            return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True), None
        except Exception:
            pass 

    # [신규 분석] 지침서 PDF 파일 읽기
    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files:
        return None, "🚨 서버에 지침서 파일(PDF)이 존재하지 않습니다."

    # 진행률 계산을 위한 전체 장수 파악
    total_pages = 0
    for f in valid_files:
        try: total_pages += len(PdfReader(f).pages)
        except: pass
            
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_text = ""
    current_page = 0
    
    # 📡 [1단계] 데이터 추출 (1% ~ 40%)
    for f in valid_files:
        reader = PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t: all_text += t
            current_page += 1
            # 실시간 퍼센트 표시 복구
            percent = int((current_page / total_pages) * 40)
            progress_bar.progress(percent / 100.0)
            status_text.markdown(f"📡 **[1/2] 지침서 데이터 분석 중: {percent}% 완료** ({current_page}/{total_pages}장 읽음)")
            
    try:
        # 텍스트 최적화 쪼개기
        splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
        chunks = splitter.split_text(all_text)
        vector_db = None
        total_chunks = len(chunks)
        
        # 🧠 [2단계] 지능형 지식 구조화 (41% ~ 100% / 시스템 보호 모드)
        for i in range(0, total_chunks, 100):
            batch = chunks[i:i+100]
            if vector_db is None:
                vector_db = FAISS.from_texts(batch, embeddings)
            else:
                vector_db.add_texts(batch)
            
            # 구조화 퍼센트 계산
            c_percent = 40 + int(((min(i + 100, total_chunks)) / total_chunks) * 60)
            progress_bar.progress(c_percent / 100.0)
            status_text.markdown(f"🧠 **[2/2] 지식 최적화 구축 중: {c_percent}% 완료** (구글 과부하 방어 중)")
            time.sleep(1.5) # [핵심] 구글 서버 기절 방지용 1.5초 휴식
            
        # 완성된 지식을 서버 하드디스크에 영구 저장 (다음 접속시 0초)
        vector_db.save_local(index_path)
        progress_bar.empty()
        status_text.empty()
        return vector_db, None
    except Exception as e:
        return None, f"❌ 데이터 구축 중 치명적 오류: {str(e)}"

# 시스템 구동
vdb, error_msg = load_or_build_vdb()

# 상단 UI 헤더 출력
st.markdown("""
<div class='enterprise-header'>
    <div>
        <div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div>
        <h1>🏅 인증조사 마스터 AI</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# 왼쪽 사이드바 설정
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): 
        st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.success("📡 **시스템 상태:** 최적화 가동 중")
    st.info(f"🔑 **작동 중인 엔진:** {len(API_KEYS)}개")
    if st.button("🔄 지식 메모리 초기화", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 에러가 있을 경우 상세 원인 출력
if error_msg:
    st.error(error_msg)
    st.stop()

# ============================================================
# 🗂️ 4. [기능] 메인 검색 및 AI 훈련 탭
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

# --- TAB 1: 규정 검색 (타이핑 답변) ---
with tab1:
    chat_box1 = st.container(height=500)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정이나 지침을 입력하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with chat_box1.chat_message("user"): st.markdown(query)
        
        with chat_box1.chat_message("assistant"):
            try:
                # 600페이지에서 근거 4개 즉시 탐색
                docs = vdb.similarity_search(query, k=4)
                context = "\n\n".join([d.page_content for d in docs])
                prompt = f"지침서 내용:\n{context}\n\n질문: {query}\n(한국어로 친절하게 답변하고 지침서의 근거를 반드시 포함해줘.)"
                
                # 실시간 타이핑 출력 시작
                stream = generate_with_retry(prompt)
                full_res = st.write_stream(stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except Exception as e:
                st.error(f"⚠️ 일시적인 지연입니다. (원인: {str(e)})")

# --- TAB 2: 감독관 훈련 (채점 및 피드백) ---
with tab2:
    st.info("💡 감독관의 질문에 답변하여 실전 대응 능력을 키우십시오.")
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    # 새로운 질문 받기 버튼
    if st.button("▶️ 새로운 감독관 현장 질문 생성", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            try:
                # 현장 질문 생성 및 타이핑 출력
                q_prompt = "병원 인증평가 감독관처럼 짧고 날카로운 현장 질문 하나만 한국어로 해줘. (예: 손 위생 시점 5가지는?)"
                stream = generate_with_retry(q_prompt)
                full_q = st.write_stream(stream)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
            except Exception:
                st.error("⚠️ 질문을 생성할 수 없습니다.")

    # 답변 입력 및 실시간 채점
    if answer := st.chat_input("답변을 입력하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": answer})
            with chat_box2.chat_message("user"): st.markdown(answer)
            
            with chat_box2.chat_message("assistant"):
                try:
                    # 지침서 내용과 답변 비교 분석
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    context = "\n\n".join([d.page_content for d in docs])
                    eval_prompt = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{answer}'\n지침서:\n{context}\n\n위 답변이 맞는지 짧게 채점하고, 지침서에 기반한 올바른 정답을 알려줘."
                    
                    # 채점 결과 스트리밍 출력
                    eval_stream = generate_with_retry(eval_prompt)
                    full_eval = st.write_stream(eval_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_eval})
                    st.session_state.current_q = None 
                except Exception:
                    st.error("⚠️ 채점 엔진에 오류가 발생했습니다.")
        else:
            st.warning("먼저 위쪽의 '질문 생성' 버튼을 눌러주세요.")
