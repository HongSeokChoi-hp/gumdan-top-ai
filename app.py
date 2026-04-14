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
# 🎨 1. [디자인/보안] 병원 전용 프리미엄 UI 및 테두리 설정
# ============================================================
# [요청사항 1] 보안 코드 설정
SET_PASSWORD = "0366"

st.set_page_config(
    page_title="검단탑병원 인증 AI 마스터", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# [요청사항 2] 검색창 진한 파란색 테두리 (#005691) 및 폰트 스타일 적용
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 상단 엔터프라이즈 헤더 디자인 [요청사항 3] */
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 30px 40px; border-radius: 15px; margin-bottom: 35px;
        box-shadow: 0 10px 30px rgba(0, 51, 145, 0.2);
    }
    .badge { 
        background: #8CC63F; color: #003366; padding: 6px 14px; 
        border-radius: 6px; font-weight: bold; margin-bottom: 12px; display: inline-block;
        font-size: 0.9rem;
    }
    .enterprise-header h1 { 
        margin: 0; font-size: 2.5rem; font-weight: 800; color: white; letter-spacing: -1.5px; 
    }

    /* [선생님 핵심 요청사항] 검색창 진한 파란색 테두리 및 그림자 효과 */
    [data-testid="stChatInput"] { 
        border: 4px solid #005691 !important; 
        border-radius: 20px !important; 
        box-shadow: 0 8px 32px rgba(0, 86, 145, 0.3) !important;
        background-color: white !important;
        padding: 10px !important;
    }
    
    /* 탭 스타일 조정 */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] {
        height: 60px; background-color: #f1f5f9; border-radius: 10px 10px 0 0; 
        padding: 0 30px; font-weight: 700; color: #64748b;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #005691 !important; color: white !important; 
    }
</style>
""", unsafe_allow_html=True)

# [요청사항 1] 접속 비밀번호 확인 로직 (보안 강화)
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
            if pwd: st.error("❌ 보안 코드가 일치하지 않습니다. 다시 시도해주십시오.")
    st.stop()

# ============================================================
# 🔑 2. [엔진] 무적의 API 키 로테이션 및 자동 모델 전환 (요청사항 5, 6)
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
if isinstance(raw_keys, str):
    API_KEYS = [k.strip() for k in raw_keys.replace("[", "").replace("]", "").replace('"', '').replace("'", "").split(",") if k.strip()]
else:
    API_KEYS = list(raw_keys)

if not API_KEYS:
    st.error("🚨 가동 가능한 AI 엔진 키가 없습니다. 관리자 설정을 확인하십시오.")
    st.stop()

def generate_with_retry(prompt_text):
    """[요청사항 12, 15] 실시간 타이핑 출력을 지원하는 2단 모델 우회 엔진"""
    keys = list(API_KEYS)
    random.shuffle(keys) # [요청사항 5] 시도시마다 무작위 키 선택
    
    for key in keys:
        try:
            genai.configure(api_key=key)
            try:
                # [요청사항 6] 1순위: 최신 2.5-Flash 모델 시도
                model = genai.GenerativeModel('gemini-2.5-flash')
                return model.generate_content(prompt_text, stream=True)
            except Exception:
                # [요청사항 6] 2순위: 에러 시 1.5-Flash 모델로 즉시 하향 우회
                model = genai.GenerativeModel('gemini-1.5-flash')
                return model.generate_content(prompt_text, stream=True)
        except ResourceExhausted:
            continue # 다음 키로 넘어감
        except Exception:
            continue
    raise Exception("모든 AI 엔진이 응답하지 않습니다. 일시적인 구글 서버 지연일 수 있습니다.")

# ============================================================
# 📚 3. [지식] 지능형 데이터 분석 및 404 차단 (요청사항 7, 8, 9, 10)
# ============================================================
@st.cache_resource
def load_or_build_vdb():
    index_path = "faiss_index_saved"
    working_key = API_KEYS[0]

    # [요청사항 7] 404 에러 원천 차단: 구글이 원하는 모든 이름 조합을 전수조사합니다.
    embeddings = None
    last_raw_error = ""

    # VIP 티어 전용 신형 이름부터 구형 이름까지 모두 찔러봅니다.
    model_name_candidates = [
        "text-embedding-004",           # 1. VIP 신형 (v1)
        "models/text-embedding-004",    # 2. VIP 신형 (풀네임)
        "embedding-001",                # 3. 표준형
        "models/embedding-001"          # 4. 표준형 (풀네임)
    ]

    for m_name in model_name_candidates:
        try:
            temp_emb = GoogleGenerativeAIEmbeddings(model=m_name, google_api_key=working_key)
            temp_emb.embed_query("test_probe") # 실제로 작동하는지 테스트
            embeddings = temp_emb
            break # 성공하면 즉시 탈출
        except Exception as e:
            last_raw_error = str(e)
            continue

    if not embeddings:
        return None, f"❌ 구글 지식 서버 연결 실패.\n상세 원인: {last_raw_error}"

    # [요청사항 8] 이미 분석된 데이터가 있다면 0초 만에 로딩! (캐싱 기술)
    if os.path.exists(index_path):
        try:
            return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True), None
        except Exception:
            pass 

    # [요청사항 4] 용어 순화: 'PDF' 대신 '인증 지침서'로 통합 관리
    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files:
        return None, "🚨 서버에 분석할 지침서 파일이 존재하지 않습니다. 파일을 확인하십시오."

    # [요청사항 9] 진행률 계산을 위한 전체 장수 파악
    total_pages = 0
    for f in valid_files:
        try: total_pages += len(PdfReader(f).pages)
        except: pass
            
    progress_bar = st.progress(0)
    status_text = st.empty()
    all_text = ""
    current_page = 0
    
    # 📡 [요청사항 9] 1단계: 지침서 데이터 추출 (1% ~ 40%)
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
                status_text.markdown(f"📡 **지침서 분석 중: {percent}% 완료** (총 {total_pages}장 중 {current_page}장 분석)")
        except:
            continue
            
    try:
        # 데이터 구조화 최적화 (950자 단위)
        splitter = RecursiveCharacterTextSplitter(chunk_size=950, chunk_overlap=150)
        chunks = splitter.split_text(all_text)
        vector_db = None
        total_chunks = len(chunks)
        
        # 🧠 [요청사항 9, 10] 2단계: 지능형 지식 최적화 (41% ~ 100%)
        for i in range(0, total_chunks, 100):
            batch = chunks[i:i+100]
            if vector_db is None:
                vector_db = FAISS.from_texts(batch, embeddings)
            else:
                vector_db.add_texts(batch)
            
            # 진행률 업데이트
            c_percent = 40 + int(((min(i + 100, total_chunks)) / total_chunks) * 60)
            progress_bar.progress(c_percent / 100.0)
            status_text.markdown(f"🧠 **지식 최적화 최적화 중: {c_percent}% 완료** (시스템 보호 가동)")
            # [요청사항 10] 구글 서버 과부하 방지용 정밀 휴식 (1.6초)
            time.sleep(1.6) 
            
        # [요청사항 8] 완성된 지식을 영구 저장하여 다음부터는 로딩 없이 0초 실행
        vector_db.save_local(index_path)
        progress_bar.empty()
        status_text.empty()
        return vector_db, None
    except Exception as e:
        return None, f"❌ 지식 구축 중 오류 발생: {str(e)}"

# [요청사항 3, 4] 시스템 메인 헤더 배지 표시
st.markdown("""
<div class='enterprise-header'>
    <div>
        <div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div>
        <h1>🏅 인증조사 마스터 AI</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# [요청사항 3] 사이드바 병원 로고 및 상태 표시
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): 
        st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.success("📡 **시스템 상태:** 정상 가동 중")
    st.info(f"🔑 **가동 엔진:** {len(API_KEYS)}개 활성화")
    if st.button("🔄 시스템 메모리 초기화", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# 시스템 지식 가동
vdb, error_msg = load_or_build_vdb()

# 오류가 있을 경우 구체적인 이유 출력
if error_msg:
    st.error(error_msg)
    st.stop()

# ============================================================
# 🗂️ 4. [요청사항 11~15] 통합 규정 검색 및 AI 감독관 훈련 탭
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

# --- TAB 1: [요청사항 11, 12] 통합 규정 검색 (실시간 답변) ---
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
                context_data = "\n\n".join([d.page_content for d in docs])
                full_prompt = f"지침서 내용:\n{context_data}\n\n질문: {query}\n(한국어로 친절하게 답변하고 지침서에 기반한 명확한 근거를 반드시 포함해줘.)"
                
                # [요청사항 12] 실시간 타이핑(스트리밍) 출력 시작
                stream_res = generate_with_retry(full_prompt)
                full_res = st.write_stream(stream_res)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except Exception:
                st.error("⚠️ 일시적인 지연입니다. 잠시 후 다시 시도해주십시오.")

# --- TAB 2: [요청사항 13, 14, 15] AI 감독관 훈련 (채점 및 피드백) ---
with tab2:
    st.info("💡 현장 감독관의 돌발 질문에 답변하여 실전 대응 능력을 테스트하십시오.")
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    # [요청사항 13] 새로운 현장 질문 받기
    if st.button("▶️ 새로운 감독관 현장 질문 생성", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            try:
                # 감독관 현장 질문 생성 및 타이핑 출력
                inspector_prompt = "병원 인증평가 감독관이 직원에게 던질법한 짧고 날카로운 현장 질문 하나만 한국어로 해줘."
                stream_q = generate_with_retry(inspector_prompt)
                full_q = st.write_stream(stream_q)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
            except Exception:
                st.error("⚠️ 질문 생성 실패.")

    # [요청사항 14, 15] 실시간 채점 및 스트리밍 결과 출력
    if answer_input := st.chat_input("감독관의 질문에 답변을 입력하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": answer_input})
            with chat_box2.chat_message("user"): st.markdown(answer_input)
            
            with chat_box2.chat_message("assistant"):
                try:
                    # 지침서 내용과 사용자 답변 비교 정밀 분석 [요청사항 14]
                    search_docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    ref_context = "\n\n".join([d.page_content for d in search_docs])
                    
                    eval_prompt = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{answer_input}'\n지침서 근거:\n{ref_context}\n\n위 지침서를 바탕으로 사용자의 답변이 맞는지 채점해주고 정답을 알려줘."
                    
                    # [요청사항 15] 채점 결과 실시간 스트리밍 출력
                    eval_stream_res = generate_with_retry(eval_prompt)
                    final_eval_res = st.write_stream(eval_stream_res)
                    st.session_state.train_msgs.append({"role": "assistant", "content": final_eval_res})
                    st.session_state.current_q = None 
                except Exception:
                    st.error("⚠️ 채점 엔진 오류.")
        else:
            st.warning("위쪽의 '질문 생성' 버튼을 먼저 눌러주십시오.")
