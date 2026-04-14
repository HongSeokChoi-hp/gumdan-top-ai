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
# 🔐 1. [요청사항 1, 2, 3] 보안 설정 및 병원 전용 UI 스타일링
# ============================================================
SET_PASSWORD = "0366"  # 선생님 전용 보안코드

st.set_page_config(
    page_title="검단탑병원 인증 AI 마스터", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# [디자인] 진한 파란색 테두리 및 프리텐다드 폰트 적용 (요청사항 2 반영)
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 상단 엔터프라이즈 헤더 디자인 */
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 25px 35px; border-radius: 15px; margin-bottom: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .badge { 
        background: #8CC63F; color: #003366; padding: 6px 14px; 
        border-radius: 6px; font-weight: bold; margin-bottom: 10px; display: inline-block;
        font-size: 0.85rem;
    }
    .enterprise-header h1 { margin: 0; font-size: 2.2rem; font-weight: 800; color: white; letter-spacing: -1px; }

    /* [핵심] 검색창 진한 파란색 테두리 (#005691) - 요청사항 2 반영 */
    [data-testid="stChatInput"] { 
        border: 3px solid #005691 !important; 
        border-radius: 15px !important; 
        box-shadow: 0 4px 20px rgba(0, 86, 145, 0.25) !important;
        background-color: white !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: #e2e8f0; border-radius: 8px 8px 0 0; padding: 0 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #005691 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# [요청사항 1] 접속 비밀번호 확인 로직
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png")
        st.subheader("🏥 시스템 보안 인증")
        pwd = st.text_input("접속 코드를 입력하십시오.", type="password", placeholder="보안 코드를 입력하세요")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            if pwd: st.error("❌ 코드가 일치하지 않습니다. 다시 확인해주세요.")
    st.stop()

# ============================================================
# 🔑 2. [요청사항 5, 6] 다중 API 키 로테이션 및 자동 우회 엔진
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
if isinstance(raw_keys, str):
    API_KEYS = [k.strip() for k in raw_keys.replace("[", "").replace("]", "").replace('"', '').replace("'", "").split(",") if k.strip()]
else:
    API_KEYS = list(raw_keys)

if not API_KEYS:
    st.error("🚨 설정된 API 키가 없습니다. Secrets 설정을 확인하십시오.")
    st.stop()

def generate_with_retry(prompt_text):
    """[요청사항 12, 15] 실시간 타이핑 출력을 지원하는 2단 우회 답변 엔진"""
    keys = list(API_KEYS)
    random.shuffle(keys) # [요청사항 5] 키 로테이션
    
    for key in keys:
        try:
            genai.configure(api_key=key)
            try:
                # [요청사항 6] 2.5 버전 우선 시도
                model = genai.GenerativeModel('gemini-2.5-flash')
                return model.generate_content(prompt_text, stream=True)
            except Exception:
                # [요청사항 6] 에러 시 1.5 버전으로 즉시 우회
                model = genai.GenerativeModel('gemini-1.5-flash')
                return model.generate_content(prompt_text, stream=True)
        except ResourceExhausted:
            continue
        except Exception:
            continue
    raise Exception("모든 엔진이 응답하지 않습니다. 일시적인 구글 서버 오류일 수 있습니다.")

# ============================================================
# 📚 3. [요청사항 7, 8, 9, 10] 지능형 지식 분석 (404 에러 원천 해결)
# ============================================================
@st.cache_resource
def load_or_build_vdb():
    index_path = "faiss_index_saved"
    working_key = API_KEYS[0]

    # [요청사항 7] 404 NOT_FOUND 해결: 유료 등급 전용 모델 'text-embedding-004' 강제 적용
    embeddings = None
    last_raw_error = ""

    # 유료 티어와 무료 티어 모델을 모두 찔러보며 에러를 피합니다.
    for m_name in ["models/text-embedding-004", "models/embedding-001", "embedding-001"]:
        try:
            temp_emb = GoogleGenerativeAIEmbeddings(model=m_name, google_api_key=working_key)
            temp_emb.embed_query("test_probe") # 찔러보기
            embeddings = temp_emb
            break
        except Exception as e:
            last_raw_error = str(e)
            continue

    if not embeddings:
        return None, f"❌ 구글 지능형 서버 연결 실패. (상세 이유: {last_raw_error})"

    # [요청사항 8] 이미 분석된 데이터가 있다면 0초 만에 로딩! (캐싱 기능)
    if os.path.exists(index_path):
        try:
            return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True), None
        except Exception:
            pass 

    # [요청사항 4] 용어 순화: 'PDF 파일' 대신 '지침서 데이터'로 표기
    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files:
        return None, "🚨 서버에 분석할 지침서 파일(PDF)이 존재하지 않습니다."

    # [요청사항 9] 진행률 계산을 위한 전체 장수 파악
    total_pages = 0
    for f in valid_files:
        try: total_pages += len(PdfReader(f).pages)
        except: pass
            
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_text = ""
    current_page = 0
    
    # 📡 [요청사항 9] 1단계: 데이터 추출 (1% ~ 40%)
    for f in valid_files:
        try:
            reader = PdfReader(f)
            for page in reader.pages:
                text_content = page.extract_text()
                if text_content: all_text += text_content
                current_page += 1
                # 실시간 퍼센트 바 업데이트
                percent = int((current_page / total_pages) * 40)
                progress_bar.progress(percent / 100.0)
                status_text.markdown(f"📡 **지침서 분석 중: {percent}% 완료** (총 {total_pages}장 중 {current_page}장 읽음)")
        except:
            continue
            
    try:
        # 데이터 쪼개기 최적화
        splitter = RecursiveCharacterTextSplitter(chunk_size=950, chunk_overlap=150)
        chunks = splitter.split_text(all_text)
        vector_db = None
        total_chunks = len(chunks)
        
        # 🧠 [요청사항 9, 10] 2단계: 지능형 지식 구조화 (41% ~ 100%)
        for i in range(0, total_chunks, 100):
            batch = chunks[i:i+100]
            if vector_db is None:
                vector_db = FAISS.from_texts(batch, embeddings)
            else:
                vector_db.add_texts(batch)
            
            # 진행률 업데이트
            c_percent = 40 + int(((min(i + 100, total_chunks)) / total_chunks) * 60)
            progress_bar.progress(c_percent / 100.0)
            status_text.markdown(f"🧠 **지식 최적화 중: {c_percent}% 완료** (구글 서버 보호 모드 가동)")
            # [요청사항 10] 구글 서버 과부하 방지용 휴식
            time.sleep(1.6) 
            
        # 완성된 지식 뇌를 영구 저장하여 다음부터는 로딩 없이 0초 만에 켜지게 함
        vector_db.save_local(index_path)
        progress_bar.empty()
        status_text.empty()
        return vector_db, None
    except Exception as e:
        return None, f"❌ 지식 구축 중 오류가 발생했습니다: {str(e)}"

# [요청사항 3, 4] 시스템 시작 및 배지 표시
st.markdown("""
<div class='enterprise-header'>
    <div>
        <div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div>
        <h1>🏅 인증조사 마스터 AI</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# [요청사항 3] 사이드바 병원 브랜딩
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): 
        st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.success("📡 **시스템 상태:** 정상 가동 중")
    st.info(f"🔑 **가동 엔진:** {len(API_KEYS)}개")
    if st.button("🔄 지식 메모리 초기화", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 시스템 구동 및 지식 불러오기
vdb, error_msg = load_or_build_vdb()

# 에러가 있을 경우 상세 원인 출력
if error_msg:
    st.error(error_msg)
    st.stop()

# ============================================================
# 🗂️ 4. [요청사항 11~15] 메인 통합 검색 및 AI 감독관 훈련 탭
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

# --- TAB 1: [요청사항 11, 12] 통합 규정 검색 (타이핑 답변) ---
with tab1:
    chat_box1 = st.container(height=520)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정이나 지침에 대해 질문하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with chat_box1.chat_message("user"): st.markdown(query)
        
        with chat_box1.chat_message("assistant"):
            try:
                # [요청사항 11] 지침서 근거 4개 즉시 탐색
                docs = vdb.similarity_search(query, k=4)
                context = "\n\n".join([d.page_content for d in docs])
                prompt = f"지침서 내용:\n{context}\n\n질문: {query}\n(한국어로 친절하게 답변하고 지침서의 근거를 반드시 포함해줘.)"
                
                # [요청사항 12] 실시간 타이핑(스트리밍) 출력 시작
                stream = generate_with_retry(prompt)
                full_res = st.write_stream(stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except Exception as e:
                st.error("⚠️ 시스템 연결이 일시적으로 지연되었습니다. 잠시 후 다시 시도해 주세요.")

# --- TAB 2: [요청사항 13, 14, 15] AI 감독관 훈련 (채점 및 피드백) ---
with tab2:
    st.info("💡 감독관의 질문에 답변하여 실제 인증조사 실전 대응 능력을 키우십시오.")
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    # [요청사항 13] 새로운 질문 받기 버튼
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

    # [요청사항 14] 답변 입력 및 실시간 채점
    if answer := st.chat_input("감독관의 질문에 답변을 입력하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": answer})
            with chat_box2.chat_message("user"): st.markdown(answer)
            
            with chat_box2.chat_message("assistant"):
                try:
                    # [요청사항 14] 지침서 내용과 사용자 답변 비교 분석
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    context = "\n\n".join([d.page_content for d in docs])
                    eval_prompt = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{answer}'\n지침서 근거:\n{context}\n\n위 지침서를 바탕으로 사용자의 답변이 맞는지 짧게 채점해주고, 부족하다면 지침서에 기반한 올바른 정답을 알려줘."
                    
                    # [요청사항 15] 채점 결과 스트리밍 출력
                    eval_stream = generate_with_retry(eval_prompt)
                    full_eval = st.write_stream(eval_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_eval})
                    st.session_state.current_q = None # 질문 완료 후 초기화
                except Exception:
                    st.error("⚠️ 채점 엔진에 일시적인 오류가 발생했습니다.")
        else:
            st.warning("먼저 위쪽의 '질문 생성' 버튼을 눌러 감독관의 질문을 받아주세요.")
