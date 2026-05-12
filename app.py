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
    page_title="검단탑병원 인증조사 AI 전문가", 
    page_icon="🏅", 
    layout="wide"
)

# ============================================================
# 🎨 [디자인 수정] 상단 인터페이스 크기 대폭 확대 및 비율 조정
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
    
    .stApp { background-color: #f8f9fa !important; }
    p, span, div, li, h1, h2, h3, h4 { color: #111827 !important; }
    
    /* 방해 요소 영구 삭제 */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton, footer { display: none !important; visibility: hidden !important; }
    
    /* 전체 컨테이너 여백 조정 */
    .block-container { 
        padding-top: 1rem !important; /* 상단 딱 붙임 방지 */
        padding-bottom: 0rem !important; 
        max-width: 1400px !important; /* PC에서 너무 퍼지지 않게 가로폭 제한 */
    }

    /* ⬆️ [확대] 상단 네이비 배너 */
    .dashboard-header { 
        background: linear-gradient(90deg, #003366 0%, #005691 100%) !important; 
        padding: 30px 40px; /* 🚨 상하좌우 여백 대폭 확대 */
        border-radius: 12px; /* 둥글기 확대 */
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); /* 그림자 강화 */
        display: flex;
        align-items: center;
        gap: 20px; /* 요소 간격 확대 */
        margin-bottom: 25px; /* 하단 마진 확대 */
    }
    .dashboard-header img { 
        height: 50px !important; /* 🚨 로고 크기 확대 */
        flex-shrink: 0; 
        background: white; 
        padding: 5px; 
        border-radius: 8px;
    } 
    .dashboard-header * { color: #ffffff !important; } 
    .dashboard-header h1 { 
        margin: 0; 
        font-size: 2rem !important; /* 🚨 타이틀 글자 크기 대폭 확대 */
        font-weight: 800; 
        letter-spacing: -1px !important;
    }

    /* ⬆️ [확대] 라디오 버튼 (모드 선택) */
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        background-color: #ffffff !important;
        padding: 15px 25px !important; /* 🚨 여백 확대 */
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 25px; /* 하단 마진 확대 */
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    div[role="radiogroup"] label { 
        font-weight: 700 !important; 
        color: #475569 !important; 
        padding: 10px 20px !important; /* 🚨 탭 크기 확대 */
        font-size: 1.1rem !important; /* 🚨 글자 크기 확대 */
    }
    div[role="radiogroup"] label[data-baseweb="radio"]:has(input[checked]) * { color: #003366 !important; }

    /* ⬆️ [확대] 환영 섹션 카드 */
    .welcome-section {
        background-color: white !important;
        padding: 40px; /* 🚨 여백 대폭 확대 */
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 30px; /* 🚨 간격 확대 */
        margin-bottom: 35px; /* 下단 마진 확대 */
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .welcome-section img { 
        height: 90px !important; /* 🚨 로고 크기 대폭 확대 */
        flex-shrink: 0; 
    }
    .welcome-section h2 { 
        color: #111827 !important; 
        margin: 0 0 15px 0; /* 下단 간격 확대 */
        font-size: 1.8rem !important; /* 🚨 글자 크기 대폭 확대 */
        font-weight: 800; 
        line-height: 1.3;
    }
    .welcome-section p { 
        color: #475569 !important; 
        margin: 0; 
        font-size: 1.15rem !important; /* 🚨 본문 글자 크기 확대 */
        line-height: 1.6; 
    }

    /* ⬆️ [확대] 자주 묻는 질문 (추천 질문 칩) */
    .quick-prompts {
        background-color: transparent;
        padding: 10px 0 30px 0; /* 🚨 하단 여백 확대 */
        margin-bottom: 20px;
    }
    .quick-prompts h4 { 
        margin: 0 0 20px 0; /* 🚨 간격 확대 */
        font-size: 1.3rem !important; /* 🚨 제목 크기 확대 */
        color: #1e293b !important; 
        font-weight: 800;
    }
    .prompt-chips { display: flex; gap: 15px; flex-wrap: wrap; }
    .prompt-chips span {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        padding: 14px 24px; /* 🚨 칩 크기 대폭 확대 (상하/좌우) */
        border-radius: 30px; /* 🚨 더 둥글게 */
        font-size: 1.05rem !important; /* 🚨 글자 크기 확대 */
        color: #005691 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        font-weight: 600;
        transition: all 0.2s;
        cursor: pointer;
    }
    .prompt-chips span:hover {
        border-color: #005691;
        background-color: #f0f9ff;
        transform: translateY(-2px);
    }

    /* 우측 AI 가이드 구조 (유지하되 크기 살짝 조정) */
    .answer-structure {
        background-color: white !important;
        padding: 30px; /* 🚨 여백 확대 */
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .answer-structure h3 { color: #003366 !important; margin: 0 0 20px 0; font-size: 1.25rem !important; font-weight: 800; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; }
    .answer-structure ul { list-style: none; padding: 0; margin: 0; }
    .answer-structure li { margin-bottom: 20px; background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #005691; }
    .answer-structure-title { font-weight: 700; color: #005691 !important; margin-bottom: 8px; font-size: 1.1rem !important;}
    .answer-structure-content { color: #475569 !important; font-size: 1rem !important; line-height: 1.6; }

    /* 채팅 메시지 영역 (글자 크기 미세 조정) */
    [data-testid="stChatMessage"] { 
        padding: 20px 25px; 
        font-size: 1rem !important;
        line-height: 1.7;
    }

    /* =================================================== */
    /* 📱 모바일 전용 UI (모바일에서는 크기 적절히 조절) */
    /* =================================================== */
    @media (max-width: 768px) {
        div[data-testid="column"]:nth-of-type(2) { display: none !important; }
        .block-container { padding-top: 0.5rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
        
        .dashboard-header { padding: 20px; margin-bottom: 15px; gap: 10px; }
        .dashboard-header img { height: 35px !important; }
        .dashboard-header h1 { font-size: 1.3rem !important; }
        
        .welcome-section { padding: 25px 20px; margin-bottom: 20px; flex-direction: column; text-align: center; gap: 15px; }
        .welcome-section img { height: 60px !important; }
        .welcome-section h2 { font-size: 1.4rem !important; margin-bottom: 8px; }
        .welcome-section p { font-size: 1rem !important; }
        
        div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) { padding: 10px !important; margin-bottom: 15px; }
        div[role="radiogroup"] label { padding: 8px 12px !important; font-size: 1rem !important; }

        .quick-prompts h4 { font-size: 1.15rem !important; margin-bottom: 15px; }
        .prompt-chips { gap: 10px; }
        .prompt-chips span { padding: 10px 16px; font-size: 0.9rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# 🔐 [인증] 로그인 로직 (유지)
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

# 🧠 [엔진] DB 로드 (유지)
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

# 상단 배너 (크기 확대 적용됨)
st.markdown(f"""
<div class='dashboard-header'>
    {logo_html}
    <h1>검단탑병원 인증조사 AI 전문가</h1>
</div>
""", unsafe_allow_html=True)

# 모드 선택
if "current_mode" not in st.session_state: st.session_state.current_mode = "🔍 인증 지침서 검색"
st.session_state.current_mode = st.radio("모드 선택", ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"], horizontal=True, label_visibility="collapsed")
mode = st.session_state.current_mode

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

# PC: 2분할 레이아웃 / 모바일: 우측 가이드 자동 숨김 처리
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
    # 환영 섹션 (크기 확대 적용됨)
    st.markdown(f"""
    <div class='welcome-section'>
        {logo_html}
        <div>
            <h2>안녕하세요! 인증조사 AI 전문가입니다</h2>
            <p>방대한 인증 지침서를 단 몇 초 만에 검색하고, AI 감독관과 함께 실전 훈련을 진행하세요.<br>지침 기반의 정확한 답변과 근거 페이지를 즉시 확인하시고 평가를 완벽하게 대비하십시오.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 💎 자주 묻는 질문 섹션 (칩 크기 확대 적용됨)
    st.markdown("""
    <div class='quick-prompts'>
        <h4>💡 이렇게 질문해 보세요 (클릭하여 복사)</h4>
        <div class='prompt-chips'>
            <span>💬 낙상 발생 시 보고 절차와 타임라인은 어떻게 되나요?</span>
            <span>💬 근접오류(Near Miss) 정의와 보고 활성화 방안은?</span>
            <span>💬 감염관리 위원회의 구성 요건과 주요 역할은 무엇인가요?</span>
            <span>💬 병동 환경 점검 체크리스트 필수 항목을 알려주세요.</span>
            <span>💬 직원의 심폐소생술(CPR) 교육 이수 기준과 유효기간은?</span>
            <span>💬 화재 발생 시 상황별 대응 매뉴얼(R.A.C.E.) 내용을 요약해줘.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if mode == "🔍 인증 지침서 검색":
        for m in st.session_state.search_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

    elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":
        st.info("💡 하단의 채팅창에 답변을 입력하면 AI가 지침서 기반으로 채점합니다.")
        if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
            with st.chat_message("assistant"):
                with st.spinner("💭 감독관이 지침서를 분석하여 질문을 생성 중..."):
                    random_docs = vdb.similarity_search(random.choice(["지침", "규정", "절차"]), k=3)
                    sample_ctx = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in random_docs])
                    q_stream = get_intelligent_response(f"인증평가 감독관 질문 1개 생성. 실제 현장에서 직원의 지침 숙지 여부를 묻는 날카로운 질문을 하세요. 특정 상황을 가정해도 좋습니다.\n내용:\n{sample_ctx}")
                    st.session_state.current_q = st.write_stream(q_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
        for m in st.session_state.train_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

with answer_col:
    # 우측 답변 가이드 (크기 미세 조정)
    st.markdown(f"""
    <div class='answer-structure'>
        <h3>🌟 AI 표준 답변 가이드</h3>
        <ul>
            <li>
                <div class='answer-structure-title'>💡 답변 요약</div>
                <div class='answer-structure-content'>핵심 내용을 2~3줄로 명확하게 요약하여 먼저 제시합니다.</div>
            </li>
            <li>
                <div class='answer-structure-title'>⚖️ 근거</div>
                <div class='answer-structure-content'>• 관련 지침서 항목 (예: 환자안전 지침서 3.4)<br>• 5주기 인증기준 번호<br>• 🚨 <strong>정확한 지침서 페이지 번호 (p.12)</strong></div>
            </li>
            <li>
                <div class='answer-structure-title'>📂 예상 확인자료</div>
                <div class='answer-structure-content'>조사위원이 현장에서 요구할 가능성이 높은 규정, 기록지, 보고서, 체크리스트 목록을 제시합니다.</div>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# 하단 채팅창 프로세스 (유지)
if query := st.chat_input("인증 지침에 관해 질문하거나 감독관의 질문에 답변하십시오..."):
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        with st.chat_message("assistant"):
            with st.spinner("💭 지침서를 분석하며 페이지 번호와 함께 답변을 정리 중..."):
                try:
                    docs = vdb.similarity_search(query, k=15) # 검색 정확도 향상을 위해 k값 증가
                    ctx_str = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
                    full_ans = st.write_stream(get_intelligent_response(f"{SYS_RULE}\n\n[원문 데이터]\n{ctx_str}\n\n질문: {query}"))
                    st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
                except Exception as e: st.error(f"🚨 오류: {e}")
    else:
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)
            with st.chat_message("assistant"):
                with st.spinner("💭 답변을 기반으로 지침서 부합 여부 채점 중..."):
                    try:
                        docs = vdb.similarity_search(st.session_state.current_q, k=10)
                        ctx_str = "\n\n".join([f"[문서 메타데이터: {d.metadata}]\n{d.page_content}" for d in docs])
                        full_ans = st.write_stream(get_intelligent_response(f"인증평가 감독관 시선에서 직원의 답변 채점 및 보완. 실제 지침서 내용 기반 피드백.\n질문: {st.session_state.current_q}\n직원 답변: {query}\n지침 데이터:\n{ctx_str}"))
                        st.session_state.train_msgs.append({"role": "assistant", "content": full_ans})
                        st.session_state.current_q = None
                    except Exception as e: st.error(f"🚨 오류: {e}")
