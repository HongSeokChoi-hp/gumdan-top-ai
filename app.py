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
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다. 설정 확인이 필요합니다.")
    st.stop()

SET_PASSWORD = "0366" 

st.set_page_config(
    page_title="검단탑병원 인증조사 AI 도우미", 
    page_icon="🏅", 
    layout="wide"
)

# ============================================================
# 🎨 [디자인 정상화] PC/모바일 완벽 호환 CSS (버그 원천 차단)
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
    
    /* 1. 기본 배경 및 폰트 컬러 (다크모드 강제 해제) */
    .stApp { background-color: #f4f7fb !important; }
    p, span, div, li, h1, h2, h3, h4 { color: #111827 !important; }
    
    /* 2. 스트림릿 기본 방해 요소 영구 삭제 */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton, footer { display: none !important; visibility: hidden !important; }
    
    /* 3. 빈공간 축소 */
    .block-container { 
        padding-top: 1rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 1200px !important; 
    }

    /* 4. 상단 네이비 배너 */
    .dashboard-header { 
        background: linear-gradient(135deg, #003366 0%, #005691 100%) !important; 
        padding: 15px 25px; 
        border-radius: 12px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }
    .dashboard-header img { height: 40px !important; flex-shrink: 0; background: white; padding: 4px; border-radius: 8px;} 
    .dashboard-header * { color: #ffffff !important; } 
    .dashboard-header h1 { margin: 0; font-size: 1.5rem !important; font-weight: 800; letter-spacing: -0.5px !important;}

    /* 5. 모드 전환 라디오 버튼 (깔끔한 탭 스타일) */
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        background-color: #ffffff !important;
        padding: 8px !important;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    div[role="radiogroup"] label { font-weight: 700 !important; color: #475569 !important; padding: 8px 15px !important; border-radius: 8px !important;}
    div[role="radiogroup"] label[data-baseweb="radio"]:has(input[checked]) { background-color: #f1f5f9 !important; }
    div[role="radiogroup"] label[data-baseweb="radio"]:has(input[checked]) * { color: #005691 !important; }

    /* 6. 환영 섹션 카드 */
    .welcome-section {
        background-color: white !important;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
        gap: 20px;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .welcome-section img { height: 60px !important; flex-shrink: 0; }
    .welcome-section h2 { color: #111827 !important; margin: 0 0 8px 0; font-size: 1.4rem; font-weight: 800;}
    .welcome-section p { color: #475569 !important; margin: 0; font-size: 1rem; line-height: 1.5;}

    /* 7. 우측 답변 구조 안내 카드 (깨졌던 부분 완벽 복구) */
    .answer-structure {
        background-color: white !important;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    .answer-structure h3 { color: #003366 !important; margin: 0 0 15px 0; font-size: 1.2rem; font-weight: 800; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; }
    .answer-structure ul { list-style: none; padding: 0; margin: 0; }
    .answer-structure li { margin-bottom: 15px; }
    .answer-structure-title { font-weight: 700; color: #005691 !important; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; font-size: 1.05rem;}
    .answer-structure-content { color: #475569 !important; font-size: 0.95rem; line-height: 1.6; background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #005691; }

    /* 🚨 8. 모바일 채팅창 시커먼 버그 완벽 해결 (순백색 고정) 🚨 */
    div[data-testid="stChatInput"] { 
        position: sticky !important; 
        bottom: 0 !important; 
        padding: 10px 0 25px 0 !important; 
        background: #f4f7fb !important; /* 바깥 배경색과 동일하게 */
        z-index: 1001 !important; 
    }
    div[data-testid="stChatInput"] > div { 
        background-color: #ffffff !important; /* 입력창 본체는 무조건 흰색 */
        border: 2px solid #cbd5e1 !important; 
        border-radius: 30px !important; 
        margin: 0 10px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: #005691 !important;
    }
    /* 글씨 색상 무조건 짙은 회색 강제 */
    div[data-testid="stChatInput"] textarea {
        color: #111827 !important; 
        -webkit-text-fill-color: #111827 !important; 
        background-color: transparent !important;
        padding: 12px 20px !important;
        font-size: 1rem !important;
    }
    ::placeholder { color: #94a3b8 !important; opacity: 1; }
    
    div[data-testid="stChatInput"] button {
        background-color: #005691 !important; 
        color: white !important;
        border-radius: 50% !important;
        padding: 6px !important;
        margin-right: 10px !important;
    }
    div[data-testid="stChatInput"] svg { fill: white !important; width: 18px !important; height: 18px !important; }

    /* 9. 채팅 메시지 말풍선 */
    [data-testid="stChatMessage"] { 
        background-color: #ffffff; 
        border-radius: 12px; 
        padding: 20px 25px; 
        box-shadow: 0 1px 4px rgba(0,0,0,0.05); 
        margin-bottom: 15px; 
        border: 1px solid #e2e8f0; 
        line-height: 1.6;
    }

    /* 📱 10. 모바일에서만 살짝 조절 (PC 레이아웃은 건드리지 않음) */
    @media (max-width: 768px) {
        .block-container { padding-top: 0.5rem !important; }
        .dashboard-header { flex-direction: column; align-items: flex-start; padding: 15px; border-radius: 8px;}
        .dashboard-header img { height: 35px !important; }
        .dashboard-header h1 { font-size: 1.2rem !important; }
        .welcome-section { flex-direction: column; text-align: center; padding: 20px; }
        .welcome-section img { height: 50px !important; }
        div[data-testid="stChatInput"] { padding-bottom: env(safe-area-inset-bottom, 20px) !important; } /* 아이폰 하단 바 대응 */
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
        st.markdown("<h3 style='text-align:center; color:#003366; font-weight:800; margin-bottom:20px;'>인증조사 AI 도우미 시스템</h3>", unsafe_allow_html=True)
        pwd = st.text_input("보안 코드 입력", type="password", placeholder="코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: 
            st.session_state.authenticated = True
            st.rerun()
        elif pwd: 
            st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# 🧠 [엔진] DB 로드
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

logo_html = ""
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}'>"

# 상단 배너
st.markdown(f"""
<div class='dashboard-header'>
    {logo_html}
    <h1>검단탑병원 인증조사 AI 전문가</h1>
</div>
""", unsafe_allow_html=True)

# 모드 선택 탭
if "current_mode" not in st.session_state: st.session_state.current_mode = "🔍 인증 지침서 검색"
st.session_state.current_mode = st.radio("모드 선택", ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"], horizontal=True, label_visibility="collapsed")
mode = st.session_state.current_mode

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# 🚨 정상적인 스트림릿 2분할 컬럼 레이아웃 (이전의 파괴적인 속성 제거)
main_col, answer_col = st.columns([2.2, 1])

SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다. 
사용자의 질문에 대해 반드시 제공된 [원문 데이터]를 분석하여 아래의 3단 구조 양식에 맞춰 답변하십시오.

### 💡 답변 요약
(질문에 대한 핵심 내용을 2~3줄로 명확하게 요약)

### ⚖️ 근거
(답변의 근거가 되는 지침서 항목, 절차서 번호 및 **정확한 페이지 번호**를 불릿 기호(•)를 사용하여 나열. 예: • 환자안전 지침서 3.4 (p.12))

### 📂 예상 확인자료
(현장 평가 시 확인하거나 준비해야 할 관련 기록지, 보고서, 체크리스트 등을 불릿 기호(•)를 사용하여 나열)
"""

with main_col:
    # 환영 섹션
    st.markdown(f"""
    <div class='welcome-section'>
        {logo_html}
        <div>
            <h2>안녕하세요! 인증조사 AI 전문가입니다</h2>
            <p>인증지침 검색, 예상질문 대비, 체크리스트 확인까지 AI와 함께 더 쉽고 빠르게!</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if mode == "🔍 인증 지침서 검색":
        for m in st.session_state.search_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":
        st.info("💡 감독관의 질문에 답변하고 지침서 기반 채점을 받아보세요.")
        if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
            with st.chat_message("assistant"):
                with st.spinner("💭 감독관이 질문을 생성하고 있습니다..."):
                    random_docs = vdb.similarity_search(random.choice(["지침", "규정"]), k=3)
                    sample_ctx = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in random_docs])
                    q_stream = get_intelligent_response(f"인증평가 감독관 질문 1개 생성. 행동 말고 규정 지식을 묻는 날카로운 질문을 하세요.\n내용:\n{sample_ctx}")
                    st.session_state.current_q = st.write_stream(q_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
        for m in st.session_state.train_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

with answer_col:
    # 우측 답변 가이드 (파괴되었던 디자인 완벽 복구)
    st.markdown(f"""
    <div class='answer-structure'>
        <h3>🌟 AI 표준 답변 가이드</h3>
        <ul>
            <li>
                <div class='answer-structure-title'>💡 답변 요약</div>
                <div class='answer-structure-content'>낙상예방을 위해 고위험 환자 평가, 환경관리, 교육 등을 시행하며 재발 방지 활동을 강화합니다.</div>
            </li>
            <li>
                <div class='answer-structure-title'>⚖️ 근거</div>
                <div class='answer-structure-content'>• 환자안전 지침서 3.4 낙상예방관리 (p.12)<br>• 5주기 인증기준 IPR.2.1 (p.45)</div>
            </li>
            <li>
                <div class='answer-structure-title'>📂 예상 확인자료</div>
                <div class='answer-structure-content'>• 낙상 고위험 환자 평가 기록지<br>• 낙상 발생 보고서 및 RCA 분석<br>• 병동 환경 점검 체크리스트</div>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 🚨 순백색으로 에러 완벽 해결된 채팅창
if query := st.chat_input("질문하거나 답변하십시오..."):
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        with st.chat_message("assistant"):
            with st.spinner("💭 지침서를 분석 중입니다..."):
                try:
                    docs = vdb.similarity_search(query, k=12)
                    ctx_str = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
                    full_ans = st.write_stream(get_intelligent_response(f"{SYS_RULE}\n\n[원문 데이터]\n{ctx_str}\n\n질문: {query}"))
                    st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
                except Exception as e: st.error(f"🚨 오류: {e}")
    else:
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)
            with st.chat_message("assistant"):
                with st.spinner("💭 답변을 채점 중입니다..."):
                    try:
                        docs = vdb.similarity_search(st.session_state.current_q, k=8)
                        ctx_str = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
                        full_ans = st.write_stream(get_intelligent_response(f"감독관 시선 채점 및 보완. 출처 금지.\n질문: {st.session_state.current_q}\n답변: {query}\n데이터:\n{ctx_str}"))
                        st.session_state.train_msgs.append({"role": "assistant", "content": full_ans})
                        st.session_state.current_q = None
                    except Exception as e: st.error(f"🚨 오류: {e}")
