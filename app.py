import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
import random
import time
import base64

# ============================================================
# 🔑 [보안] Secrets 및 API 키 연동
# ============================================================
try:
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다. 설정 확인이 필요합니다.")
    st.stop()

# 시스템 보안 코드
SET_PASSWORD = "0366" 

# 기본 페이지 설정 (반응형 와이드 레이아웃)
st.set_page_config(
    page_title="검단탑병원 인증조사 AI 전문가", 
    page_icon="🏅", 
    layout="wide", 
    initial_sidebar_state="auto"
)

# ============================================================
# 🎨 [디자인] 상하단 고정 및 모바일 가독성 최적화 CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    /* 앱 전체 배경색 고정 */
    .stApp { background-color: #F8FAFC !important; }
    
    /* 일반 텍스트 색상 강제 고정 (다크모드 방어) */
    p, span, div, li, h1, h2, h3, h4 { color: #111827 !important; }
    
    /* 스트림릿 기본 헤더 및 푸터 완벽 은폐 */
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton, footer { display: none !important; visibility: hidden !important; }
    
    /* 메인 컨테이너 상하 여백 제거 */
    .block-container { 
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important; 
        margin-top: 0px !important; 
    }

    /* 🚨 상단 초슬림 헤더 디자인 */
    .enterprise-header { 
        background: linear-gradient(135deg, #002b5e 0%, #005691 100%); 
        padding: 12px 18px; 
        border-radius: 10px; 
        margin-top: 0px;
        margin-bottom: 5px;
        box-shadow: 0 4px 10px rgba(0, 86, 145, 0.1);
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .enterprise-header * { color: #ffffff !important; } /* 배너 내부 텍스트 흰색 강제 */
    .enterprise-header h1 { margin: 0; font-size: 1.25rem !important; font-weight: 800; }
    .enterprise-header img { height: 26px !important; } 

    /* 🚨 상단 인터페이스(타이틀 + 모드전환) 천장 영구 고정 */
    div[data-testid="stVerticalBlock"] > div:has(.enterprise-header) {
        position: sticky !important;
        top: 0 !important;
        z-index: 1000 !important;
        background-color: #F8FAFC !important; 
        padding-top: 15px !important;
    }
    
    /* 모드 전환 라디오 버튼 고정 */
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        position: sticky !important;
        top: 72px !important; 
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
    div[role="radiogroup"] label { margin: 0 !important; font-weight: 700 !important; cursor: pointer; }

    /* 🚨 하단 입력창 바닥 고정 및 가독성 최적화 */
    div[data-testid="stVerticalBlockOuter"] { min-height: 100dvh; display: flex; flex-direction: column; }
    div[data-testid="stVerticalBlock"] { flex-grow: 1 !important; }

    div[data-testid="stChatInput"] { 
        position: sticky !important; 
        bottom: 0 !important; 
        padding-bottom: 30px !important;
        padding-top: 15px !important;
        background-color: #F8FAFC !important; 
        z-index: 1001 !important; 
        margin-top: auto !important;
    }
    
    /* 입력창 테두리 및 배경색 고정 */
    div[data-testid="stChatInput"] > div { border: 2px solid #005691 !important; border-radius: 20px !important; background-color: #ffffff !important; }
    
    /* 🚨 모바일 다크모드 글자색 증발 완벽 방지 (강제 하양배경/검정글씨) */
    [data-testid="stChatInput"] div[data-baseweb="textarea"], 
    [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important; 
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important; 
    }

    /* 채팅 말풍선 디자인 */
    [data-testid="stChatMessage"] { 
        background-color: #ffffff; 
        border-radius: 12px; 
        padding: 15px 20px; 
        box-shadow: 0 1px 4px rgba(0,0,0,0.05); 
        margin-bottom: 12px; 
        border: 1px solid #e2e8f0; 
    }
    
    /* 출처 목록 스타일 */
    .source-box {
        font-size: 0.85rem;
        color: #64748b;
        background-color: #f1f5f9;
        padding: 10px;
        border-radius: 8px;
        margin-top: 15px;
        border-left: 4px solid #005691;
    }
</style>
""", unsafe_allow_html=True)

# 🔐 [인증] 로그인 로직
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
            st.error("❌ 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🧠 [엔진] 지능형 검색 및 AI 답변 로직
# ============================================================
@st.cache_resource
def load_intelligent_db():
    if not os.path.exists("faiss_index_saved"): 
        return None, "faiss_index_saved 폴더를 찾을 수 없습니다."
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=random.choice(API_KEYS))
        vdb = FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
        return vdb, None
    except Exception as e:
        return None, f"데이터베이스 로드 실패: {e}"

vdb, db_status_msg = load_intelligent_db()

if not vdb:
    st.error(f"🚨 시스템 오류: {db_status_msg}")
    st.stop()

def get_intelligent_response(prompt_text):
    time.sleep(1.2) # 자연스러운 응답 속도 조절
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=random.choice(API_KEYS),
        temperature=0.1 # 팩트 유지 및 오타 교정을 위한 최소 지능
    )
    for chunk in llm.stream(prompt_text):
        if chunk.content:
            yield chunk.content

# ============================================================
# 🗂️ [메인] 시스템 인터페이스
# ============================================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): 
        st.image("검단탑병원-로고_고화질.png")
    st.markdown("### 📡 실시간 모니터링")
    st.success("인증 지침서 데이터 동기화 완료")
    st.info("v2.6.5-Final | 90% 정확도 보정 모드")

# 상단 배너 로고 처리
logo_html = ""
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}' style='height:26px; background-color:white; padding:3px; border-radius:4px;'>"

# 상단 헤더 출력
st.markdown(f"""
<div class='enterprise-header'>
    {logo_html}
    <h1>검단탑병원 인증조사 AI 전문가</h1>
</div>
""", unsafe_allow_html=True)

# 모드 전환 스위치 (상단 고정됨)
mode = st.radio("모드 선택", ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"], horizontal=True, label_visibility="collapsed")

# 세션 관리
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# 🚨 [AI 뇌 개편] 90% 일치 + 핸드북 우선 + 출처 명시
SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다.
1. 지침서 질문 시 [원문 데이터]를 90% 이상 그대로 인용하십시오. 
2. 단, 원문의 깨진 글자(Ÿ, O 등)와 엉망인 줄바꿈은 읽기 좋게 문맥을 다듬으십시오.
3. **가장 중요:** 데이터 중 '핸드북(Handbook)' 내용이 있다면 이를 답변의 최우선 뼈대로 삼으십시오.
4. 문장 끝에 [근거 1], [근거 2] 표시를 하고, 답변 맨 아래에 반드시 [📚 출처 목록]을 만들어 실제 파일명을 나열하십시오.
5. 데이터에 없는 내용은 절대 상상하지 마십시오."""

# ------------------------------------------------------------
# 🔍 모드 1: 지침서 검색 화면
# ------------------------------------------------------------
if mode == "🔍 인증 지침서 검색":
    for m in st.session_state.search_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

# ------------------------------------------------------------
# 🕵️‍♂️ 모드 2: 모의훈련 화면
# ------------------------------------------------------------
elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":
    st.info("💡 실제 인증평가 감독관이 던질만한 질문에 답변하고 피드백을 받아보세요.")
    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        with st.chat_message("assistant"):
            q_gen_prompt = "병원 인증평가 감독관이 현장 직원에게 던질법한 날카로운 질문 1개만 생성하시오. 질문만 짧게 하시오."
            q_stream = get_intelligent_response(q_gen_prompt)
            st.session_state.current_q = st.write_stream(q_stream)
            st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
            
    for m in st.session_state.train_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

# ------------------------------------------------------------
# 🚨 [공통] 하단 고정 입력창 및 지능형 검색 로직
# ------------------------------------------------------------
placeholder = "규정 질문 또는 가볍게 인사를 건네보세요..." if mode == "🔍 인증 지침서 검색" else "감독관 질문에 답변하십시오..."

if query := st.chat_input(placeholder):
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        
        with st.chat_message("assistant"):
            try:
                # 🚨 정확도 롤백 (k=6으로 집중 검색)
                docs = vdb.similarity_search(query, k=6)
                
                # 출처 메타데이터 추출 로직
                ctx_list = []
                for i, d in enumerate(docs):
                    source_path = d.metadata.get('source', '지침서 원문.pdf')
                    file_name = os.path.basename(source_path) # 파일명만 추출
                    ctx_list.append(f"[근거 {i+1} | 출처: {file_name}]\n{d.page_content}")
                
                context_str = "\n\n".join(ctx_list)
                final_prompt = f"{SYS_RULE}\n\n[원문 데이터]\n{context_str}\n\n사용자 질문: {query}"
                
                res_stream = get_intelligent_response(final_prompt)
                full_ans = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
            except Exception as e:
                st.error(f"🚨 답변 생성 중 오류 발생: {e}")

    else: # 모의훈련 모드 답변 처리
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)
            
            with st.chat_message("assistant"):
                try:
                    docs = vdb.similarity_search(st.session_state.current_q, k=4)
                    ctx_list = [f"[출처: {os.path.basename(d.metadata.get('source', '원문.pdf'))}]\n{d.page_content}" for d in docs]
                    context_str = "\n\n".join(ctx_list)
                    
                    eval_prompt = f"엄격한 감독관의 시선으로 채점(100점 만점)하고 보완하세요. 답변 하단에 [📚 출처 목록]을 반드시 작성해.\n질문: {st.session_state.current_q}\n답변: {query}\n원문 참고:\n{context_str}"
                    res_stream = get_intelligent_response(eval_prompt)
                    full_ans = st.write_stream(res_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_ans})
                    st.session_state.current_q = None
                except Exception as e:
                    st.error(f"🚨 채점 중 오류 발생: {e}")
        else:
            st.warning("먼저 '질문 생성' 버튼을 눌러주세요.")
