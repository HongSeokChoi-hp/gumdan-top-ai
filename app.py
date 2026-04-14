import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os

# ============================================================
# 🎨 1. 안전한 화면 설정 및 잔재물 제거
# ============================================================
SET_PASSWORD = "0366" 
st.set_page_config(page_title="검단탑병원 인증 AI 마스터", page_icon="🏅", layout="wide", initial_sidebar_state="collapsed")

# [수정] PC 화면을 하얗게 날려버린 위험한 CSS 코드를 삭제하고, 메뉴와 로고만 정밀하게 숨깁니다.
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 스트림릿 우측 상단 메뉴, 깃허브 아이콘, 연필 아이콘 삭제 */
    #MainMenu, header, footer {visibility: hidden !important; display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    
    /* 모바일 우측 하단 프로필/왕관 배지(viewerBadge) 정확히 타겟팅하여 삭제 */
    .viewerBadge_container__1QSob, .viewerBadge_link__1S137, #viewerBadge {display: none !important;}
    
    /* 기본 레이아웃 디자인 */
    .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}
    .enterprise-header { background: linear-gradient(135deg, #003366 0%, #005691 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 20px;}
    .enterprise-header h1 { margin: 0; font-size: 2rem; color: white; font-weight: 900;}
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f1f5f9; border-radius: 10px 10px 0 0; padding: 0 20px; font-weight: bold; color: #64748b;}
    .stTabs [aria-selected="true"] { background-color: #005691 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# 🔐 로그인 
if not st.session_state.get("authenticated", False):
    st.markdown("<h3 style='text-align:center; margin-top:20px; color:#003366; font-weight:800;'>인증 AI 마스터 접속</h3>", unsafe_allow_html=True)
    pwd = st.text_input("보안코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
    if pwd == SET_PASSWORD: 
        st.session_state.authenticated = True
        st.rerun()
    elif pwd: 
        st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🔑 2. 모바일 무한 로딩 방지 엔진 (직관적 에러 표출)
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

if not API_KEYS: st.error("🚨 API 키가 설정되지 않았습니다."); st.stop()

def generate_answer(prompt_text):
    genai.configure(api_key=API_KEYS[0])
    # [수정] 속도가 훨씬 빠르고 모바일 환경에서 뻗지 않는 1.5-flash 모델로 변경
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        # 무한 루프 삭제. 에러가 나면 숨기지 않고 즉시 화면에 이유를 보여줍니다.
        response = model.generate_content(prompt_text, stream=False)
        return response.text
    except Exception as e:
        return f"❌ 구글 서버 응답 지연 (원인: {str(e)}) - 잠시 후 다시 질문해주세요."

# ============================================================
# 📚 3. 0초 지식 로딩
# ============================================================
@st.cache_resource
def load_vdb():
    if not os.path.exists("faiss_index_saved"): return None, "faiss_index_saved 폴더를 찾을 수 없습니다."
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=API_KEYS[0])
        return FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True), None
    except Exception as e:
        return None, str(e)

st.markdown("<div class='enterprise-header'><h1>🏅 검단탑병원 인증조사 마스터 AI</h1></div>", unsafe_allow_html=True)

vdb, error_msg = load_vdb()
if error_msg: st.error("🚨 지식 데이터베이스 연결 실패: " + error_msg); st.stop()

# ============================================================
# 🗂️ 4. 통합 규정 검색 및 훈련 (동문서답 방지 프롬프트 유지)
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

SYS_PROMPT = "당신은 검단탑병원의 인증평가 컨설턴트입니다. 아래 [지침서 내용]을 바탕으로 중복되는 내용을 하나로 묶어 명확하게 요약하여 답변하세요. 기계적으로 내용을 복사하지 마세요."

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

with tab1:
    chat_box1 = st.container(height=400)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정이나 지침을 질문하십시오..."):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with chat_box1.chat_message("user"): st.markdown(query)
        
        with chat_box1.chat_message("assistant"):
            with st.spinner("지침서 분석 및 답변 생성 중..."):
                docs = vdb.similarity_search(query, k=3)
                ctx = "\n\n".join([d.page_content for d in docs])
                ans = generate_answer(f"{SYS_PROMPT}\n\n[지침서 내용]\n{ctx}\n\n사용자 질문: {query}")
                st.markdown(ans)
                st.session_state.search_msgs.append({"role": "assistant", "content": ans})

with tab2:
    chat_box2 = st.container(height=400)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        with chat_box2.chat_message("assistant"):
            with st.spinner("질문 생성 중..."):
                q = generate_answer("병원 인증평가 감독관이 던질법한 짧은 현장 질문 딱 1개만 해줘.")
                st.markdown(q)
                st.session_state.current_q = q
                st.session_state.train_msgs.append({"role": "assistant", "content": q})

    if ans_in := st.chat_input("답변을 입력하십시오..."):
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": ans_in})
            with chat_box2.chat_message("user"): st.markdown(ans_in)
            with chat_box2.chat_message("assistant"):
                with st.spinner("채점 중..."):
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    ctx = "\n\n".join([d.page_content for d in docs])
                    eval_ans = generate_answer(f"{SYS_PROMPT}\n\n[지침서 내용]\n{ctx}\n\n감독관 질문: '{st.session_state.current_q}'\n사용자 답변: '{ans_in}'\n이 답변이 맞는지 지침서에 기반해 채점해주세요.")
                    st.markdown(eval_ans)
                    st.session_state.train_msgs.append({"role": "assistant", "content": eval_ans})
                    st.session_state.current_q = None 
        else: st.warning("먼저 질문 생성 버튼을 눌러주십시오.")
