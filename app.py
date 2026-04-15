import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
import random
import time

# ============================================================
# 🔑 Secrets 완벽 연동 (유지)
# ============================================================
try:
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다.")
    st.stop()

SET_PASSWORD = "0366" 

# 페이지 기본 설정 (고급화)
st.set_page_config(page_title="검단탑병원 지능형 지식화", page_icon="🏅", layout="wide", initial_sidebar_state="collapsed")

# ============================================================
# 🎨 프리미엄 UI 커스텀 & 스트림릿 마크(깃허브/왕관) 원천 차단
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 🚨 1. 깃허브 마크, 상단 메뉴바(Header) 완전 삭제 */
    [data-testid="stHeader"] { display: none !important; }
    
    /* 🚨 2. 우측 하단 빨간 왕관(Creator Badge), Deploy 버튼 완전 삭제 */
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton, [data-testid="manage-app-button"] { display: none !important; visibility: hidden !important; }
    iframe[src*="badge"] { display: none !important; }

    /* 3. 검색창 디자인 고급화 (진한 파란색 테두리 및 그림자) */
    [data-testid="stChatInput"] { 
        border: 2px solid #005691 !important; 
        border-radius: 20px !important; 
        box-shadow: 0 4px 15px rgba(0, 86, 145, 0.1) !important;
    }

    /* 4. 메인 헤더 배너 고급화 */
    .enterprise-header { 
        background: linear-gradient(135deg, #002b5e 0%, #005691 100%); 
        color: white; 
        padding: 20px 25px; 
        border-radius: 16px; 
        margin-bottom: 20px;
        margin-top: 10px;
        box-shadow: 0 10px 30px rgba(0, 86, 145, 0.2);
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .enterprise-header h1 { margin: 0; font-size: 1.6rem; font-weight: 900; letter-spacing: -0.5px; }
    
    /* 5. 모바일 탭 글씨 잘림 방지 및 카톡 스타일 여백 최적화 */
    button[data-baseweb="tab"] { font-size: 0.95rem !important; font-weight: 700; padding: 10px 15px !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; max-width: 900px !important; }
    
    /* 6. 챗봇 메시지 버블 고급화 */
    [data-testid="stChatMessage"] { background-color: #ffffff; border-radius: 12px; padding: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 10px; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# 🔐 로그인 페이지 고급화
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; font-weight:800; margin-bottom:20px;'>인증 지능형 지식화 시스템</h3>", unsafe_allow_html=True)
        pwd = st.text_input("인증코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        elif pwd: st.error("❌ 인증 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🧠 엔진 로드 (정상 통과 유지)
# ============================================================
@st.cache_resource
def load_intelligent_db():
    if not os.path.exists("faiss_index_saved"): 
        return None, "faiss_index_saved 폴더가 없습니다."
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=random.choice(API_KEYS))
        vdb = FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
        return vdb, None
    except Exception as e:
        return None, f"DB 로드 실패: {e}"

vdb, db_status_msg = load_intelligent_db()

if not vdb:
    st.error(f"🚨 지식화 엔진 로딩 실패: {db_status_msg}")
    st.stop()

# ============================================================
# 🎯 [정확도 극대화] LLM 프롬프트 및 설정 강화
# ============================================================
def get_intelligent_response(prompt_text):
    time.sleep(1.6)
    
    # 🚨 정확도를 위해 temperature를 0.0으로 고정 (창의성 배제, 팩트 위주)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=random.choice(API_KEYS),
        temperature=0.0 
    )
    for chunk in llm.stream(prompt_text):
        if chunk.content:
            yield chunk.content

# ============================================================
# 🗂️ 메인 시스템 UI 구성
# ============================================================
# 로고를 헤더 안으로 삽입하여 모바일에서도 무조건 고급스럽게 보이도록 설정
logo_html = ""
import base64
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}' style='height:40px; background-color:white; padding:5px; border-radius:8px;'>"

st.markdown(f"""
<div class='enterprise-header'>
    {logo_html}
    <h1>검단탑병원 인증 지능형 지식화</h1>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관"])

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# 🚨 프롬프트 강력 통제: 구체적이고 상세하게 답변하도록 강제
SYS_RULE = """당신은 검단탑병원 인증평가 최고 책임 컨설턴트입니다.
반드시 제공된 [인증 지침서 원문]에만 근거하여 답변하십시오. 원문에 없는 내용은 절대 지어내지 마십시오.
[지시사항]
1. 두리뭉실한 답변을 금지합니다.
2. 지침서 내의 '구체적인 절차, 예외 상황, 기준 수치 및 예시'를 빠짐없이 추출하십시오.
3. 읽기 쉽게 불릿 기호(-, *, 1. 2. 3.)를 사용하여 체계적이고 상세하게 설명하십시오."""

with tab1:
    # 🚨 불필요한 빈 컨테이너(height=450)를 삭제하여 카톡처럼 자연스러운 인터페이스 구현
    for m in st.session_state.search_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정이나 지침에 대해 질문하십시오...", key="q_search"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        
        with st.chat_message("assistant"):
            try:
                # 검색 정확도를 높이기 위해 참조 문서 수를 5개로 증가
                docs = vdb.similarity_search(query, k=5)
                ctx = "\n\n".join([f"[근거 {i+1}]: {d.page_content}" for i, d in enumerate(docs)])
                
                res_stream = get_intelligent_response(f"{SYS_RULE}\n\n[원문 데이터]\n{ctx}\n\n질문: {query}")
                full_ans = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
            except Exception as e:
                st.error(f"🚨 답변 생성 오류: {e}")

with tab2:
    st.info("💡 모의 감독관이 무작위로 던지는 현장 질문에 답변하여 채점을 받아보세요.")
    for m in st.session_state.train_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])
        
    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        with st.chat_message("assistant"):
            try:
                q_stream = get_intelligent_response("병원 인증평가 감독관이 현장 직원에게 던질법한 날카로운 질문 1개만 생성하시오.")
                st.session_state.current_q = st.write_stream(q_stream)
                st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
            except Exception as e:
                st.error(f"🚨 질문 생성 오류: {e}")
            
    if ans_input := st.chat_input("감독관 질문에 답변하십시오...", key="q_train"):
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": ans_input})
            with st.chat_message("user"): st.markdown(ans_input)
            with st.chat_message("assistant"):
                try:
                    docs = vdb.similarity_search(st.session_state.current_q, k=4)
                    ctx = "\n\n".join([d.page_content for d in docs])
                    eval_p = f"{SYS_RULE}\n\n질문: {st.session_state.current_q}\n직원 답변: {ans_input}\n원문:\n{ctx}\n\n이 답변을 지침서 기반으로 엄격하게 채점(100점 만점)하고, 누락된 핵심 내용을 상세히 보완하여 설명해줘."
                    res_stream = get_intelligent_response(eval_p)
                    eval_ans = st.write_stream(res_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": eval_ans})
                    st.session_state.current_q = None
                except Exception as e:
                    st.error(f"🚨 채점 오류: {e}")
