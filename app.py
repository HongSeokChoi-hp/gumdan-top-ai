import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import random

# ============================================================
# 🎨 1. [디자인/보안] 병원 전용 프리미엄 UI 및 테두리 설정
# ============================================================
SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증 AI 마스터", page_icon="🏅", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    .enterprise-header { background: linear-gradient(135deg, #003366 0%, #005691 100%); color: white; padding: 45px 55px; border-radius: 20px; margin-bottom: 45px; box-shadow: 0 15px 50px rgba(0, 51, 145, 0.35); }
    .badge { background: #8CC63F; color: #003366; padding: 10px 20px; border-radius: 8px; font-weight: bold; margin-bottom: 20px; display: inline-block; font-size: 1rem; }
    .enterprise-header h1 { margin: 0; font-size: 3.2rem; font-weight: 900; color: white; letter-spacing: -2px; }
    [data-testid="stChatInput"] { border: 4px solid #005691 !important; border-radius: 20px !important; box-shadow: 0 15px 55px rgba(0, 86, 145, 0.4) !important; background-color: white !important; padding: 18px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 30px; }
    .stTabs [data-baseweb="tab"] { height: 75px; background-color: #f1f5f9; border-radius: 15px 15px 0 0; padding: 0 50px; font-weight: 800; color: #64748b; font-size: 1.3rem; }
    .stTabs [aria-selected="true"] { background-color: #005691 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
        st.markdown("<h2 style='text-align:center;'>🏥 검단탑병원 인증 AI 시스템</h2>", unsafe_allow_html=True)
        pwd = st.text_input("접속 코드를 입력하십시오.", type="password", placeholder="보안 코드를 입력하세요")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        else:
            if pwd: st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🔑 2. API 키 및 답변 엔진 (글자만 쏙쏙 뽑는 로직 완벽 적용)
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

if not API_KEYS: st.error("🚨 설정된 API 키가 없습니다."); st.stop()

def generate_with_retry(prompt_text):
    keys = list(API_KEYS)
    random.shuffle(keys)
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt_text, stream=True)
            
            # [핵심] JSON 포장지를 뜯고 순수 한글 텍스트만 추출하는 제너레이터
            def text_extractor():
                for chunk in response:
                    try:
                        if chunk.text:
                            yield chunk.text
                    except Exception:
                        pass
            return text_extractor()
            
        except Exception:
            continue # 에러 나면 다음 키로 재시도
            
    raise Exception("모든 AI 엔진이 응답하지 않습니다.")

# ============================================================
# 📚 3. 0초 로딩 (서버 과부하 원천 차단)
# ============================================================
@st.cache_resource
def load_vdb():
    if not os.path.exists("faiss_index_saved"):
        return None, "🚨 서버에 'faiss_index_saved' 지식 폴더가 없습니다."
    
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=API_KEYS[0])
        return FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True), None
    except Exception as e:
        return None, f"지식 데이터 연결 실패: {str(e)}"

st.markdown("<div class='enterprise-header'><div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div><h1>🏅 인증조사 마스터 AI</h1></div>", unsafe_allow_html=True)

with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.success("📡 **시스템 상태: 정상 작동 중**")

vdb, error_msg = load_vdb()
if error_msg: st.error(error_msg); st.stop()

# ============================================================
# 🗂️ 4. 통합 규정 검색 및 훈련
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

with tab1:
    chat_box1 = st.container(height=520)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    # 업데이트 확인용 텍스트 추가 (이 글자가 보이면 새 버전 적용 완료!)
    if query := st.chat_input("규정이나 지침에 대해 질문하십시오... (최적화 완료)", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with chat_box1.chat_message("user"): st.markdown(query)
        with chat_box1.chat_message("assistant"):
            try:
                docs = vdb.similarity_search(query, k=4)
                context_data = "\n\n".join([d.page_content for d in docs])
                stream_res = generate_with_retry(f"지침서 내용:\n{context_data}\n\n질문: {query}\n(한국어로 친절하게 답변하고 근거 포함)")
                full_res = st.write_stream(stream_res)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
            except Exception as e:
                st.error("⚠️ 시스템 지연입니다. 잠시 후 시도해주세요.")

with tab2:
    st.info("💡 현장 감독관의 질문에 답변하여 실전 능력을 테스트하십시오.")
    chat_box2 = st.container(height=450)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    if st.button("▶️ 새로운 감독관 현장 질문 생성", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            try:
                stream_q = generate_with_retry("병원 인증평가 감독관이 던질법한 짧은 현장 질문 하나 해줘.")
                full_q = st.write_stream(stream_q)
                st.session_state.current_q = full_q
                st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
            except:
                st.error("⚠️ 질문 생성 실패.")

    # 업데이트 확인용 텍스트 추가
    if answer_input := st.chat_input("답변을 입력하십시오... (최적화 완료)", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": answer_input})
            with chat_box2.chat_message("user"): st.markdown(answer_input)
            with chat_box2.chat_message("assistant"):
                try:
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    ref_ctx = "\n\n".join([d.page_content for d in docs])
                    eval_stream = generate_with_retry(f"질문: '{st.session_state.current_q}'\n답변: '{answer_input}'\n지침서:\n{ref_ctx}\n\n채점하고 정답 알려줘.")
                    final_eval = st.write_stream(eval_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": final_eval})
                    st.session_state.current_q = None 
                except:
                    st.error("⚠️ 채점 엔진 오류.")
        else: st.warning("먼저 질문 생성 버튼을 눌러주십시오.")
