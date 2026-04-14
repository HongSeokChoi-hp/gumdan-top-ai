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
# 🔑 2. 시크릿 키 파싱 & 로테이션 엔진
# ==========================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
if isinstance(raw_keys, str):
    API_KEYS = [k.strip() for k in raw_keys.replace("[", "").replace("]", "").replace('"', '').replace("'", "").split(",") if k.strip()]
else:
    API_KEYS = list(raw_keys)

if not API_KEYS:
    st.error("❌ 구글 API 키가 설정되지 않았습니다. Secrets 메뉴를 확인해주세요.")
    st.stop()

def generate_with_retry(prompt_text):
    keys = list(API_KEYS)
    random.shuffle(keys)
    
    last_error = None
    for key in keys:
        try:
            genai.configure(api_key=key)
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                return model.generate_content(prompt_text, stream=True) # 스트리밍(타이핑) 출력 적용
            except Exception as inner_e:
                if "404" in str(inner_e) or "not found" in str(inner_e).lower():
                    model = genai.GenerativeModel('gemini-1.5-flash') # 2.5 막히면 1.5로 즉시 우회
                    return model.generate_content(prompt_text, stream=True)
                raise inner_e
        except ResourceExhausted:
            continue
        except Exception as e:
            last_error = e
            continue
    raise Exception("현재 등록된 모든 API 키의 한도가 초과되었거나 응답이 없습니다.")

# ==========================================
# 📚 3. 지식 DB 구축 (퍼센트 복구 + 정밀 에러 보고)
# ==========================================
@st.cache_resource
def load_or_build_vdb():
    index_path = "faiss_index_saved"
    working_key = random.choice(API_KEYS)

    # [핵심 복구] 통신 에러를 파일 에러로 착각하지 않도록 임베딩 3중 방어막 적용
    embeddings = None
    for m_name in ["models/embedding-001", "models/text-embedding-004", "embedding-001"]:
        try:
            temp_emb = GoogleGenerativeAIEmbeddings(model=m_name, google_api_key=working_key)
            temp_emb.embed_query("test") # 찔러보기
            embeddings = temp_emb
            break
        except: pass

    if not embeddings:
        return None, "❌ 구글 서버가 임베딩 모델 연결을 거부했습니다. API 키의 권한 문제일 수 있습니다."

    # 1. 저장된 뇌(캐시)가 있으면 로딩 0초로 바로 불러오기
    if os.path.exists(index_path):
        try:
            return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True), None
        except: pass 

    # 2. 파일 존재 여부 명확히 확인
    pdf_files = ["guide.pdf", "manual2.pdf"]
    valid_files = [f for f in pdf_files if os.path.exists(f)]
    if not valid_files:
        return None, "🚨 서버(GitHub)에 'guide.pdf' 또는 'manual2.pdf' 파일이 올라가 있지 않습니다."

    total_pages = 0
    for f in valid_files:
        try: total_pages += len(PdfReader(f).pages)
        except: pass
        
    if total_pages == 0: 
        return None, "🚨 PDF 파일 안에서 텍스트를 하나도 읽어낼 수 없습니다. 파일이 손상되었는지 확인하세요."

    progress_bar = st.progress(0)
    status_text = st.empty()
    all_text = ""
    current_page = 0
    
    # 3. 텍스트 추출 (퍼센트: 1% ~ 40%)
    for f in valid_files:
        try:
            reader = PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t: all_text += t
                
                current_page += 1
                percent = int((current_page / total_pages) * 40)
                progress_bar.progress(percent / 100.0)
                status_text.markdown(f"📡 **[1/2] 지침서 분석 중: {percent}% 완료** ({current_page}/{total_pages}장 읽음)")
        except: continue
            
    try:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=100)
        chunks = text_splitter.split_text(all_text)
        
        vector_db = None
        total_chunks = len(chunks)
        
        # 4. 데이터 구조화 (퍼센트: 41% ~ 100% / 과부하 방지 1.5초 휴식)
        for i in range(0, total_chunks, 100):
            batch = chunks[i:i+100]
            if vector_db is None:
                vector_db = FAISS.from_texts(batch, embeddings)
            else:
                vector_db.add_texts(batch)
                
            chunk_percent = 40 + int(((min(i + 100, total_chunks)) / total_chunks) * 60)
            progress_bar.progress(chunk_percent / 100.0)
            status_text.markdown(f"🧠 **[2/2] 지식 구조화 중: {chunk_percent}% 완료** (구글 과부하 방지 안전 모드)")
            time.sleep(1.5)
            
        vector_db.save_local(index_path) # 영구 저장
        progress_bar.empty()
        status_text.empty()
        return vector_db, None
    except Exception as e:
        status_text.empty()
        progress_bar.empty()
        if "quota" in str(e).lower() or "429" in str(e):
            return None, "⚠️ 구글 API 일일 사용량이 모두 초과되었습니다. 내일 다시 시도하거나 키를 추가하세요."
        return None, f"❌ 데이터 구조화 중 오류 발생: {e}"

vdb_result, error_msg = load_or_build_vdb()

# 상단 헤더
st.markdown("<div class='enterprise-header'><div><div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div><h1>🏅 인증조사 마스터 AI</h1></div></div>", unsafe_allow_html=True)

with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.info(f"📡 **시스템 상태:** 최적화 대기 중\n\n🔑 가동 중인 AI 엔진: {len(API_KEYS)}개")
    if st.button("🔄 시스템 메모리 정리", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# [핵심] 이제 에러가 나면 엉뚱한 소리 안 하고 진짜 원인을 화면에 띄웁니다.
if error_msg:
    st.error(error_msg)
    st.stop()

vdb = vdb_result

# ==========================================
# 🗂️ 4. 메인 탭 로직 (모든 기능 포함 및 스트리밍)
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
                
                # 타이핑 치듯 스트리밍 출력
                res_stream = generate_with_retry(prompt)
                full_res = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except Exception as e:
                st.error(f"⚠️ 시스템 응답 지연: {e}")

# --- TAB 2: 감독관 훈련 ---
with tab2:
    st.info("💡 실전 대응 능력을 키우기 위해 감독관의 질문에 답변해 보세요.")
    
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    if st.button("▶️ 새로운 감독관 질문 받기", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            try:
                # 타이핑 치듯 스트리밍 출력
                res_stream = generate_with_retry("인증평가 감독관처럼 짧고 핵심적인 현장 질문 하나만 한국어로 해줘. 다른 말은 하지마.")
                full_q = st.write_stream(res_stream)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
            except Exception as e:
                st.error("⚠️ 엔진 사용량이 초과되었을 수 있습니다.")
                st.session_state.current_q = None

    if train_prompt := st.chat_input("감독관의 질문에 답변하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": train_prompt})
            with chat_box2.chat_message("user"): st.markdown(train_prompt)
            with chat_box2.chat_message("assistant"):
                try:
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    context = "\n\n".join([doc.page_content for doc in docs])
                    eval_prompt = f"질문: '{st.session_state.current_q}'\n사용자 답변: '{train_prompt}'\n[지침서 근거]\n{context}\n\n위 지침서를 바탕으로 답변이 맞는지 짧게 평가해주고 정답을 알려줘."
                    
                    # 평가 결과도 타이핑 치듯 스트리밍 출력
                    res_eval_stream = generate_with_retry(eval_prompt)
                    full_eval = st.write_stream(res_eval_stream)
                    
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_eval})
                    st.session_state.current_q = None 
                except Exception as e:
                    st.error("⚠️ 평가를 생성할 수 없습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.warning("먼저 위쪽의 '▶️ 새로운 감독관 질문 받기' 버튼을 눌러 질문을 받아주세요.")
