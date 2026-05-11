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
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ============================================================
# 🎨 [디자인 끝판왕] 대시보드 최고급 스타일 CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
    
    /* 전체 배경색 아주 연한 파스텔톤으로 변경 */
    .stApp { background-color: #F4F7FB !important; }
    p, span, div, li, h1, h2, h3, h4 { color: #1e293b !important; }
    
    /* 기본 스트림릿 요소 숨기기 */
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton, footer { display: none !important; visibility: hidden !important; }
    
    .block-container { 
        padding-top: 1.5rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 1400px !important; /* 화면을 너무 넓지 않게 잡아줌 */
    }

    /* 💎 상단 헤더/배너 고급화 */
    .dashboard-header { 
        background: linear-gradient(to right, #ffffff, #f8fafc); 
        padding: 18px 30px; 
        border-radius: 16px; 
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .dashboard-header img { height: 45px !important; flex-shrink: 0; } 
    .dashboard-header h1 { 
        margin: 0; 
        font-size: 1.6rem !important; 
        font-weight: 800; 
        color: #003366 !important; 
        letter-spacing: -0.5px !important; 
    }

    /* 💎 사이드바 깔끔하게 정돈 */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
        box-shadow: 2px 0 10px rgba(0,0,0,0.02);
    }
    [data-testid="stSidebar"] hr { border-color: #f1f5f9; }

    /* 💎 환영 섹션 고급화 */
    .welcome-section {
        background: linear-gradient(135deg, #005691 0%, #003366 100%);
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0, 86, 145, 0.15);
        display: flex;
        align-items: center;
        gap: 25px;
        margin-bottom: 25px;
        color: white !important;
    }
    .welcome-section * { color: white !important; }
    .welcome-section img { height: 70px !important; background: white; padding: 10px; border-radius: 12px; }
    .welcome-section h2 { margin: 0 0 10px 0; font-size: 1.8rem; font-weight: 800; }
    .welcome-section p { margin: 0; opacity: 0.9; font-size: 1.05rem; line-height: 1.5; }

    /* 💎 그리드 카드 애니메이션 및 그림자 강화 */
    .grid-section {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin-bottom: 30px;
    }
    .grid-card {
        background-color: white !important;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border: 1px solid #e2e8f0;
        text-align: left;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .grid-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 20px rgba(0, 86, 145, 0.08);
        border-color: #005691;
    }
    .grid-card-icon { font-size: 2.2rem; margin-bottom: 15px; color: #005691 !important; }
    .grid-card-title { font-weight: 800; font-size: 1.1rem; margin-bottom: 8px; }
    .grid-card-desc { color: #64748b !important; font-size: 0.95rem; line-height: 1.4; }

    /* 💎 오른쪽 답변 구조 예시 (프리미엄 카드 느낌) */
    .answer-structure {
        background-color: white !important;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        border: 1px solid #e2e8f0;
        position: sticky;
        top: 20px;
    }
    .answer-structure h3 { color: #003366 !important; margin: 0 0 20px 0; font-size: 1.2rem; font-weight: 800; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; }
    .answer-structure ul { list-style: none; padding: 0; margin: 0; }
    .answer-structure li { margin-bottom: 20px; background: #f8fafc; padding: 15px; border-radius: 10px; border-left: 4px solid #005691; }
    .answer-structure-title { font-weight: 800; color: #005691 !important; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;}
    .answer-structure-content { color: #475569 !important; font-size: 0.95rem; line-height: 1.6; }

    /* 💎 플로팅 스타일 채팅 입력창 끝판왕 */
    div[data-testid="stChatInput"] { 
        position: sticky !important; 
        bottom: 0 !important; 
        padding: 20px 0 30px 0 !important; 
        background: linear-gradient(to top, #F4F7FB 80%, transparent) !important; 
        z-index: 1001 !important; 
    }
    div[data-testid="stChatInput"] > div { 
        background-color: #ffffff !important; 
        border: 2px solid #cbd5e1 !important; 
        border-radius: 30px !important; 
        margin: 0 10px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08) !important;
        transition: border-color 0.3s;
    }
    div[data-testid="stChatInput"] > div:focus-within {
        border-color: #005691 !important;
    }
    div[data-testid="stChatInput"] textarea {
        color: #1e293b !important; 
        -webkit-text-fill-color: #1e293b !important; 
        padding: 15px 20px !important;
        font-size: 1.05rem !important;
    }
    div[data-testid="stChatInput"] button {
        background-color: #005691 !important; 
        color: white !important;
        border-radius: 50% !important;
        padding: 8px !important;
        margin-right: 10px !important;
        transition: transform 0.2s, background-color 0.2s;
    }
    div[data-testid="stChatInput"] button:hover {
        background-color: #003366 !important;
        transform: scale(1.05);
    }
    
    /* 💎 채팅 메시지 말풍선 세련되게 다듬기 */
    [data-testid="stChatMessage"] { 
        background-color: #ffffff; 
        border-radius: 16px; 
        padding: 20px 25px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.04); 
        margin-bottom: 15px; 
        border: 1px solid #e2e8f0; 
        line-height: 1.6;
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

# 🗂️ [메인 UI]
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): 
        st.image("검단탑병원-로고_고화질.png")
    st.markdown("### 🛰️ 메뉴")
    st.markdown("- 🏠 홈")
    st.markdown("- ❓ AI 질문하기")
    st.markdown("- 🎯 예상질문")
    st.markdown("- 📝 체크리스트")
    st.markdown("- 📂 준비자료")
    st.markdown("- 🗣️ 모의면담")
    st.markdown("- 🧩 교육퀴즈")
    st.markdown("- ⭐ 즐겨찾기")
    st.markdown("- 📊 관리자 통계")
    st.markdown("---")
    st.markdown("### 📢 실시간 상태")
    st.success("지침서 데이터 동기화 완료")

logo_html = ""
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}' style='height:45px; background-color:transparent;'>"

st.markdown(f"""
<div class='dashboard-header'>
    {logo_html}
    <h1>검단탑병원 인증조사 AI 도우미</h1>
</div>
""", unsafe_allow_html=True)

main_col, answer_col = st.columns([2.2, 1])

with main_col:
    mode = st.radio("모드 선택", ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"], horizontal=True, label_visibility="collapsed")

    st.markdown(f"""
    <div class='welcome-section'>
        {logo_html}
        <div>
            <h2>안녕하세요! 인증조사 AI 도우미입니다</h2>
            <p>인증지침 검색, 예상질문 대비, 체크리스트 확인까지<br>인증조사 준비를 AI와 함께 더 쉽고 빠르게 진행하세요.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class='grid-section'>
        <div class='grid-card'>
            <div class='grid-card-icon'>❓</div>
            <div class='grid-card-title'>조사위원 예상질문</div>
            <div class='grid-card-desc'>낙상, 감염, 환자안전 등<br>분야별 예상질문 확인</div>
        </div>
        <div class='grid-card'>
            <div class='grid-card-icon'>📝</div>
            <div class='grid-card-title'>부서별 체크리스트</div>
            <div class='grid-card-desc'>부서별 인증 기준 및<br>체크리스트 확인</div>
        </div>
        <div class='grid-card'>
            <div class='grid-card-icon'>📂</div>
            <div class='grid-card-title'>준비자료 확인</div>
            <div class='grid-card-desc'>현장확인 및 면담 시<br>필요한 자료 확인</div>
        </div>
        <div class='grid-card'>
            <div class='grid-card-icon'>🗣️</div>
            <div class='grid-card-title'>모의면담 시작</div>
            <div class='grid-card-desc'>실제 조사 상황을 가정한<br>모의면담 연습</div>
        </div>
        <div class='grid-card'>
            <div class='grid-card-icon'>🧩</div>
            <div class='grid-card-title'>OX 교육퀴즈</div>
            <div class='grid-card-desc'>핵심 기준과 지침을 OX 퀴즈로<br>학습하고 실력을 점검</div>
        </div>
        <div class='grid-card'>
            <div class='grid-card-icon'>⭐</div>
            <div class='grid-card-title'>즐겨찾기 & 최근 질문</div>
            <div class='grid-card-desc'>자주 찾는 항목과 최근<br>질문/답변 확인</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
    if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
    if "current_q" not in st.session_state: st.session_state.current_q = None

    # 🚨 AI 답변 구조 3단 강제 룰 적용
    SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다. 
    사용자의 질문에 대해 반드시 제공된 [원문 데이터]를 분석하여 아래의 3단 구조 양식에 맞춰 답변하십시오.

    ### 💡 답변 요약
    (질문에 대한 핵심 내용을 2~3줄로 명확하게 요약)

    ### ⚖️ 근거
    (답변의 근거가 되는 지침서 항목, 절차서 번호, 또는 인증기준을 불릿 기호(•)를 사용하여 나열)

    ### 📂 예상 확인자료
    (현장 평가 시 확인하거나 준비해야 할 관련 기록지, 보고서, 체크리스트 등을 불릿 기호(•)를 사용하여 나열)
    """

    if mode == "🔍 인증 지침서 검색":
        for m in st.session_state.search_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":
        st.info("💡 감독관의 질문에 답변하고 지침서 기반 채점을 받아보세요.")
        if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
            with st.chat_message("assistant"):
                with st.spinner("💭 감독관이 질문을 생성하고 있습니다..."):
                    random_docs = vdb.similarity_search(random.choice(["지침", "규정"]), k=3)
                    sample_ctx = "\n".join([d.page_content for d in random_docs])
                    q_stream = get_intelligent_response(f"인증평가 감독관 질문 1개 생성. 행동 말고 규정 지식을 묻는 날카로운 질문을 하세요.\n내용:\n{sample_ctx}")
                    st.session_state.current_q = st.write_stream(q_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
        for m in st.session_state.train_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

with answer_col:
    st.markdown(f"""
    <div class='answer-structure'>
        <h3>🌟 AI 답변 구조 안내</h3>
        <ul>
            <li>
                <div class='answer-structure-title'>💡 답변 요약</div>
                <div class='answer-structure-content'>낙상예방을 위해 고위험 환자 평가, 환경관리, 교육 등을 시행하며 재발 방지 활동을 강화합니다.</div>
            </li>
            <li>
                <div class='answer-structure-title'>⚖️ 근거</div>
                <div class='answer-structure-content'>• 환자안전 지침서 3.4 낙상예방관리<br>• 5주기 인증기준 IPR.2.1</div>
            </li>
            <li>
                <div class='answer-structure-title'>📂 예상 확인자료</div>
                <div class='answer-structure-content'>• 낙상 고위험 환자 평가 기록지<br>• 낙상 발생 보고서 및 RCA 분석<br>• 병동 환경 점검 체크리스트</div>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if query := st.chat_input("질문하거나 답변하십시오..."):
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        with st.chat_message("assistant"):
            with st.spinner("💭 지침서를 분석하며 3단 양식으로 정리중..."):
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
                with st.spinner("💭 답변을 기반으로 채점중..."):
                    try:
                        docs = vdb.similarity_search(st.session_state.current_q, k=8)
                        ctx_str = "\n\n".join([d.page_content for d in docs])
                        full_ans = st.write_stream(get_intelligent_response(f"감독관 시선 채점 및 보완. 출처 금지.\n질문: {st.session_state.current_q}\n답변: {query}\n데이터:\n{ctx_str}"))
                        st.session_state.train_msgs.append({"role": "assistant", "content": full_ans})
                        st.session_state.current_q = None
                    except Exception as e: st.error(f"🚨 오류: {e}")
