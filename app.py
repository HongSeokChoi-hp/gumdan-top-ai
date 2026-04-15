import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
import random
import time
import base64

# ============================================================
# 🔑 [보안] Streamlit Secrets 및 API 키 연동
# ============================================================
try:
    # 여러 개의 API 키 중 랜덤 선택하여 부하 분산
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다. 설정 확인이 필요합니다.")
    st.stop()

# 시스템 보안 코드 (기획자 설정)
SET_PASSWORD = "0366" 

# 페이지 전체 설정 (와이드 레이아웃 및 반응형 설정)
st.set_page_config(
    page_title="검단탑병원 인증조사 AI 전문가", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="auto"
)

# ============================================================
# 🎨 [디자인] 상하단 고정 및 모바일 가독성 최적화 CSS (강력 수정 반영)
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    /* 앱 전체 배경색 및 폰트색 고정 (다크모드 대응) */
    .stApp { background-color: #F8FAFC !important; }
    p, span, div, li, h1, h2, h3, h4 { color: #111827 !important; }
    
    /* 상단 기본 메뉴 및 불필요한 배너 제거 */
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton, footer { display: none !important; visibility: hidden !important; }
    
    /* 메인 화면 여백 제거 */
    .block-container { 
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important; 
        margin-top: 0px !important; 
    }

    /* 🚨 [수정 1] 상단 배너: 모바일에서도 한 줄로 나오도록 강력 고정 */
    .enterprise-header { 
        background: linear-gradient(135deg, #002b5e 0%, #005691 100%); 
        padding: 10px 15px; 
        border-radius: 10px; 
        margin-top: 0px;
        margin-bottom: 5px;
        box-shadow: 0 4px 10px rgba(0, 86, 145, 0.1);
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
        box-sizing: border-box;
    }
    .enterprise-header * { color: #ffffff !important; } 
    .enterprise-header h1 { 
        margin: 0; 
        font-size: 1.1rem !important; /* 모바일을 위해 크기 살짝 더 축소 */
        font-weight: 800; 
        white-space: nowrap !important; /* 줄바꿈 절대 방지 */
        letter-spacing: -0.7px !important; /* 자간 축소 */
        overflow: hidden;
        text-overflow: ellipsis; /* 혹시 넘치면 말줄임표 처리 */
    }
    
    /* 더 작은 모바일 기기 대응 */
    @media screen and (max-width: 360px) {
        .enterprise-header h1 { font-size: 0.95rem !important; }
    }

    .enterprise-header img { height: 22px !important; } 

    /* 상단 인터페이스 천장 영구 고정 (스티키) */
    div[data-testid="stVerticalBlock"] > div:has(.enterprise-header) {
        position: sticky !important;
        top: 0 !important;
        z-index: 1000 !important;
        background-color: #F8FAFC !important; 
        padding-top: 15px !important;
    }
    
    /* 모드 전환 스위치 고정 */
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        position: sticky !important;
        top: 68px !important; 
        z-index: 999 !important;
        background-color: #F8FAFC !important;
        padding-bottom: 12px !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }

    /* 라디오 버튼(스위치) 스타일 */
    div[role="radiogroup"] {
        background-color: #e2e8f0;
        padding: 6px;
        border-radius: 14px;
        display: inline-flex;
        gap: 10px;
    }
    div[role="radiogroup"] label { margin: 0 !important; font-weight: 700 !important; }

    /* 🚨 하단 고정 입력창 및 레이아웃 설정 */
    div[data-testid="stVerticalBlockOuter"] { min-height: 100dvh; display: flex; flex-direction: column; }
    div[data-testid="stVerticalBlock"] { flex-grow: 1 !important; }

    /* 🚨 [수정 2] 입력창 인터페이스: 꺾쇠([]) 기호 및 테두리 잔상 '완전 박멸' */
    div[data-testid="stChatInput"] { 
        position: sticky !important; 
        bottom: 0 !important; 
        padding-bottom: 30px !important;
        padding-top: 15px !important;
        background-color: #F8FAFC !important; 
        z-index: 1001 !important; 
        margin-top: auto !important;
    }
    
    /* 꺾쇠([]) 모양을 만드는 모든 요소를 투명하게 처리 */
    div[data-testid="stChatInput"] * {
        border-color: transparent !important;
        outline: none !important;
        box-shadow: none !important;
    }

    /* 바깥쪽 파란 테두리만 우리가 원하는 대로 다시 설정 */
    div[data-testid="stChatInput"] > div { 
        border: 2px solid #005691 !important; 
        border-radius: 20px !important; 
        background-color: #ffffff !important;
    }
    
    /* 내부 꺾쇠 요소 숨기기 */
    div[data-testid="stChatInput"] div[data-baseweb="textarea"]::before,
    div[data-testid="stChatInput"] div[data-baseweb="textarea"]::after,
    div[data-testid="stChatInput"] div[data-baseweb="base-input"]::before,
    div[data-testid="stChatInput"] div[data-baseweb="base-input"]::after {
        display: none !important;
    }

    /* 모바일 다크모드 글자색 보정 */
    [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important; 
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important; 
    }

    /* 채팅 말풍선 고급 디자인 */
    [data-testid="stChatMessage"] { 
        background-color: #ffffff; 
        border-radius: 12px; 
        padding: 15px 20px; 
        box-shadow: 0 1px 4px rgba(0,0,0,0.05); 
        margin-bottom: 12px; 
        border: 1px solid #e2e8f0; 
    }
</style>
""", unsafe_allow_html=True)

# 🔐 [인증] 로그인 페이지 로직
if not st.session_state.get("authenticated", False):
    st.write("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): 
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; font-weight:800; margin-bottom:20px;'>인증조사 AI 전문가 시스템</h3>", unsafe_allow_html=True)
        pwd = st.text_input("보안 코드 입력", type="password", placeholder="코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: 
            st.session_state.authenticated = True
            st.rerun()
        elif pwd: 
            st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🧠 [엔진] 검색 엔진 로드 및 AI 답변 로직
# ============================================================
@st.cache_resource
def load_intelligent_db():
    if not os.path.exists("faiss_index_saved"): 
        return None, "faiss_index_saved 데이터가 없습니다."
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=random.choice(API_KEYS))
        vdb = FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
        return vdb, None
    except Exception as e:
        return None, f"데이터베이스 로드 실패: {e}"

vdb, db_status_msg = load_intelligent_db()

if not vdb:
    st.error(f"🚨 엔진 가동 실패: {db_status_msg}")
    st.stop()

def get_intelligent_response(prompt_text):
    time.sleep(1.0) 
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=random.choice(API_KEYS),
        temperature=0.0 
    )
    for chunk in llm.stream(prompt_text):
        if chunk.content:
            yield chunk.content

# ============================================================
# 🗂️ [메인 UI] 시스템 인터페이스 배치
# ============================================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): 
        st.image("검단탑병원-로고_고화질.png")
    st.markdown("### 📡 실시간 상태")
    st.success("인증 지침서 데이터 동기화 완료")
    st.info("v2.7.0 풀버전 복구 완료")

logo_html = ""
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}' style='height:26px; background-color:white; padding:3px; border-radius:4px;'>"

st.markdown(f"""
<div class='enterprise-header'>
    {logo_html}
    <h1>검단탑병원 인증조사 AI 전문가</h1>
</div>
""", unsafe_allow_html=True)

mode = st.radio("모드 선택", ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"], horizontal=True, label_visibility="collapsed")

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다.
1. 질문에 대해 [원문 데이터]를 바탕으로 핵심 정답만 짧게 대답하십시오.
2. 답변 끝에 [근거], [출처], 파일명 등을 표시하지 마십시오.
3. 데이터 중 'manual2.pdf'가 있다면 이를 최우선 근거로 삼으십시오."""

# 🔍 모드 1: 지침서 검색
if mode == "🔍 인증 지침서 검색":
    for m in st.session_state.search_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

# 🕵️‍♂️ 모드 2: 모의훈련
elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":
    st.info("💡 감독관의 질문에 답변하고 지침서 기반 채점을 받아보세요.")
    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        with st.chat_message("assistant"):
            random_docs = vdb.similarity_search(random.choice(["지침", "규정", "절차"]), k=3)
            sample_ctx = "\n".join([d.page_content for d in random_docs])
            q_stream = get_intelligent_response(f"인증평가 감독관으로서 지침서 내용을 바탕으로 짧은 규정 질문 1개를 만드세요.\n내용:\n{sample_ctx}")
            st.session_state.current_q = st.write_stream(q_stream)
            st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
    for m in st.session_state.train_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

# 🚨 [공통 로직] 하단 고정 입력창 및 답변 프로세스
if query := st.chat_input("질문하거나 답변하십시오..."):
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        with st.chat_message("assistant"):
            try:
                docs = vdb.similarity_search(query, k=12)
                ctx_str = "\n\n".join([d.page_content for d in docs])
                full_ans = st.write_stream(get_intelligent_response(f"{SYS_RULE}\n\n[원문 데이터]\n{ctx_str}\n\n질문: {query}"))
                st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
            except Exception as e: st.error(f"🚨 오류: {e}")
    else:
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)
            with st.chat_message("assistant"):
                try:
                    docs = vdb.similarity_search(st.session_state.current_q, k=8)
                    ctx_str = "\n\n".join([d.page_content for d in docs])
                    eval_prompt = f"엄격한 감독관 시선으로 답변 채점 및 보완. 출처 표시 금지.\n질문: {st.session_state.current_q}\n답변: {query}\n참고:\n{ctx_str}"
                    full_ans = st.write_stream(get_intelligent_response(eval_prompt))
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_ans})
                    st.session_state.current_q = None
                except Exception as e: st.error(f"🚨 오류: {e}")
