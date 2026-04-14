import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import random

# ============================================================
# 🎨 1. 안전한 화면 설정 및 거머리 로고(배지) 완전 파괴
# ============================================================
SET_PASSWORD = "0366" 
st.set_page_config(page_title="검단탑병원 인증 AI 마스터", page_icon="🏅", layout="wide", initial_sidebar_state="collapsed")

# [핵심] 스트림릿이 강제로 덮어씌우는 홍보 배지를 정규식(Wildcard)으로 찾아내어 흔적도 없이 파괴합니다.
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 🚫 1. 상단 메뉴, 툴바, 헤더, 푸터 완전 삭제 */
    header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
    }
    
    /* 🔥 2. 모바일 하단 프로필/로고(거머리 배지) 극단적 파괴 */
    /* 스트림릿 서버가 강제로 쏘는 모든 요소를 크기 0, 투명도 0, 화면 밖으로 추방 */
    div[class*="viewerBadge"],
    div[id*="viewerBadge"],
    iframe[src*="streamlit"],
    iframe[title*="streamlit"],
    iframe[src*="badge"],
    a[href*="streamlit"],
    .stDeployButton {
        display: none !important;
        opacity: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
        width: 0px !important;
        height: 0px !important;
        position: absolute !important;
        z-index: -9999 !important;
    }
    
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
# 🔑 2. 모바일 무한 로딩 방지 엔진 
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

if not API_KEYS: st.error("🚨 API 키가 설정되지 않았습니다."); st.stop()

def generate_answer(prompt_text):
    genai.configure(api_key=API_KEYS[0])
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
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
# 🗂️ 4. 통합 규정 검색 및 훈련 (소설 쓰기/환각 원천 차단)
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# [핵심] AI가 절대 지어내지 못하도록 강력한 족쇄(규칙)를 채웠습니다.
SYS_PROMPT = """[최고 보안 규칙: 상상 및 날조 절대 금지]
당신은 검단탑병원의 인증평가 지침서 데이터베이스입니다.
1. 오직 아래 [제공된 지침서 원문]의 내용만을 사용하여 답변하십시오.
2. 질문에 대한 답이 [제공된 지침서 원문]에 없다면, 절대 지어내거나 외부 지식을 사용하지 말고 "해당 내용은 제공된 지침서에서 찾을 수 없습니다."라고만 명확히 답변하십시오.
3. 지침서 내용을 당신의 마음대로 해석하거나 변형하지 마십시오. 원문의 팩트와 절차를 그대로 전달하되, 중복되는 내용은 하나로 묶어 번호 매기기 등으로 요약만 하십시오.
4. 절대로 '❌' 같은 이모티콘 기호만 덜렁 출력하지 마십시오. 완전한 문장으로 설명하십시오.
"""

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

with tab1:
    chat_box1 = st.container(height=400)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정이나 지침을 질문하십시오..."):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with chat_box1.chat_message("user"): st.markdown(query)
        
        with chat_box1.chat_message("assistant"):
            with st.spinner("지침서 원문을 스캔 중입니다..."):
                docs = vdb.similarity_search(query, k=4)
                ctx = "\n\n".join([d.page_content for d in docs])
                ans = generate_answer(f"{SYS_PROMPT}\n\n[제공된 지침서 원문]\n{ctx}\n\n[사용자 질문]: {query}")
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
                with st.spinner("지침서 기반으로 채점 중..."):
                    docs = vdb.similarity_search(st.session_state.current_q, k=3)
                    ctx = "\n\n".join([d.page_content for d in docs])
                    eval_ans = generate_answer(f"{SYS_PROMPT}\n\n[제공된 지침서 원문]\n{ctx}\n\n[상황]: 감독관 질문 '{st.session_state.current_q}'에 대해 직원이 '{ans_in}'이라고 답변했습니다. 이 답변이 맞는지 제공된 원문에 기반해 채점하고 정답을 알려주세요.")
                    st.markdown(eval_ans)
                    st.session_state.train_msgs.append({"role": "assistant", "content": eval_ans})
                    st.session_state.current_q = None 
        else: st.warning("먼저 질문 생성 버튼을 눌러주십시오.")
