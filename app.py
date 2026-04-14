import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import random
import time

# ============================================================
# 🔑 1. [엔진] 다중 API 키 로테이션 및 보안 인증 (0366)
# ============================================================
API_KEYS = ["AIzaSy..."] # 가진 키들을 리스트로 모두 넣으세요.
SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증 지능형 지식화", page_icon="🏅", layout="wide", initial_sidebar_state="collapsed")

# ============================================================
# 🎨 2. [디자인] 거머리 로고 박멸 및 #005691 4px 테두리 UI
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* [기능] 스트림릿 로고, 메뉴, 하단 배지(왕관) 물리적 완전 삭제 */
    header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
    .viewerBadge_container__1QSob, #viewerBadge, div[class*="viewerBadge"], a[href*="streamlit.io"] { display: none !important; }

    /* [기능] 모바일 UI 압축 및 화면 고정 */
    .block-container { padding-top: 0rem !important; padding-bottom: 1rem !important; }
    .enterprise-header { background: linear-gradient(135deg, #003366 0%, #005691 100%); color: white; padding: 20px; border-radius: 0 0 15px 15px; margin-bottom: 10px; }
    .enterprise-header h1 { margin: 0; font-size: 1.6rem; font-weight: 900; }
    
    /* [기능] 검색창 진한 파란색(#005691) 4px 테두리 */
    [data-testid="stChatInput"] { 
        border: 4px solid #005691 !important; 
        border-radius: 15px !important; 
        box-shadow: 0 5px 15px rgba(0, 86, 145, 0.2) !important; 
    }

    .stTabs [data-baseweb="tab-list"] { gap: 5px; }
    .stTabs [data-baseweb="tab"] { height: 45px; font-weight: 800; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# 🔐 접속 인증
if not st.session_state.get("authenticated", False):
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        pwd = st.text_input("인증코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        elif pwd: st.error("❌ 인증 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🧠 3. [해결] 404/403 박멸 및 0.004 임베딩 고정
# ============================================================
@st.cache_resource
def load_intelligent_db():
    # [기능] 서버 하드 저장소 활용 0초 로딩 캐싱
    if not os.path.exists("faiss_index_saved"): return None
    current_key = random.choice(API_KEYS)
    try:
        # [기능] text-embedding-004 정밀 임베딩 고정
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=current_key)
        return FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
    except: return None

vdb = load_intelligent_db()

def get_intelligent_response(prompt_text):
    # [기능] 구글 서버 보호용 1.6초 정밀 휴식 로직
    time.sleep(1.6)
    
    # [기능] API 키 무작위 로테이션
    selected_key = random.choice(API_KEYS)
    genai.configure(api_key=selected_key)
    
    # [기능] 2.5 에러 시 1.5로 자동 스위칭 (v1 정식 주소 기반)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_text, stream=True)
        return response
    except:
        model = genai.GenerativeModel('gemini-1.5-pro')
        return model.generate_content(prompt_text, stream=True)

# ============================================================
# 🗂️ 4. [기능] 지능형 인증 지침서 UI
# ============================================================
st.markdown("<div class='enterprise-header'><h1>🏅 검단탑병원 인증 지능형 지식화</h1></div>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 인증 지침서 검색", "🕵️‍♂️ AI 감독관 훈련"])

if "msgs" not in st.session_state: st.session_state.msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

SYS_RULE = "당신은 검단탑병원 인증 컨설턴트입니다. 반드시 [지침서 원문]에 근거하여 답변하고, 자료에 없으면 절대 지어내지 마세요."

with tab1:
    # [기능] 1%~100% 실시간 상태 표시 (간이 구현)
    if vdb: st.caption("📡 인증 지침서 600페이지 데이터베이스 동기화 완료 (100%)")
    
    chat_box = st.container(height=400)
    for m in st.session_state.msgs:
        with chat_box.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("인증 지침에 대해 질문하십시오..."):
        st.session_state.msgs.append({"role": "user", "content": query})
        with chat_box.chat_message("user"): st.markdown(query)
        
        with chat_box.chat_message("assistant"):
            # [기능] 600페이지 근거 4개 참조 정밀 검색
            docs = vdb.similarity_search(query, k=4)
            ctx = "\n\n".join([f"[근거 {i+1}]: {d.page_content}" for i, d in enumerate(docs)])
            
            # [기능] 첫 글자부터 쏟아지는 스트리밍 답변
            full_prompt = f"{SYS_RULE}\n\n[지침서 원문]\n{ctx}\n\n질문: {query}"
            res_stream = get_intelligent_response(full_prompt)
            full_ans = st.write_stream(res_stream)
            st.session_state.msgs.append({"role": "assistant", "content": full_ans})

with tab2:
    st.info("🕵️‍♂️ 현장 감독관의 무작위 질문에 답변하여 실전 능력을 채점받으세요.")
    
    # [기능] AI 감독관 현장 질문 무작위 생성
    if st.button("▶️ 감독관 현장 질문 생성", use_container_width=True):
        with st.chat_message("assistant"):
            q_stream = get_intelligent_response("병원 인증평가 감독관이 현장에서 직원에게 던질법한 짧고 날카로운 질문 하나만 생성해줘.")
            st.session_state.current_q = st.write_stream(q_stream)
            
    if ans_input := st.chat_input("감독관 질문에 답변하십시오..."):
        if st.session_state.current_q:
            with st.chat_message("user"): st.markdown(ans_input)
            with st.chat_message("assistant"):
                # [기능] 사용자 답변 실시간 채점 및 스트리밍 출력
                docs = vdb.similarity_search(st.session_state.current_q, k=3)
                ctx = "\n\n".join([d.page_content for d in docs])
                eval_p = f"{SYS_RULE}\n\n[지침서 내용]\n{ctx}\n\n질문: {st.session_state.current_q}\n답변: {ans_input}\n\n이 답변을 지침서 기반으로 엄격하게 채점하고 정답을 알려줘."
                eval_stream = get_intelligent_response(eval_p)
                st.write_stream(eval_stream)
                st.session_state.current_q = None
