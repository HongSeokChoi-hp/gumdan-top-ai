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
# 🎨 [디자인 끝판왕] 정직하고 고급스러운 엔터프라이즈 스타일 CSS
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; box-sizing: border-box; }
    
    /* 전체 배경은 아주 차분하고 고급스러운 라이트 그레이 */
    .stApp { background-color: #f8f9fa !important; }
    p, span, div, li, h1, h2, h3, h4 { color: #1e293b !important; }
    
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton, footer { display: none !important; visibility: hidden !important; }
    
    .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 0rem !important; 
        max-width: 1400px !important; 
    }

    /* 💎 사이드바 정직하고 깔끔하게 정돈 */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e9ecef;
        box-shadow: 2px 0 15px rgba(0,0,0,0.02);
    }
    
    /* 모드 전환 라디오 버튼 고급화 */
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        background-color: #ffffff !important;
        padding: 10px 15px !important;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }
    div[role="radiogroup"] label { font-weight: 700 !important; color: #003366 !important; }

    /* 💎 메인 웰컴 배너 (딥 네이비 톤으로 무게감 부여) */
    .premium-welcome {
        background: linear-gradient(135deg, #001f3f 0%, #003366 100%);
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 15px 30px rgba(0, 31, 63, 0.15);
        display: flex;
        align-items: center;
        gap: 30px;
        margin-bottom: 30px;
    }
    .premium-welcome img { height: 75px !important; background: white; padding: 12px; border-radius: 16px; }
    .premium-welcome-text h2 { color: #ffffff !important; margin: 0 0 10px 0; font-size: 2rem; font-weight: 800; letter-spacing: -0.5px; }
    .premium-welcome-text p { color: #e2e8f0 !important; margin: 0; font-size: 1.1rem; line-height: 1.6; font-weight: 300; }

    /* 💎 진짜 기능 2개 집중 조명 카드 (가짜 6구역 삭제) */
    .real-features-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 25px;
        margin-bottom: 30px;
    }
    .feature-card {
        background-color: white !important;
        padding: 30px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .feature-card::before {
        content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #005691;
    }
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.08);
    }
    .feature-card h3 { margin: 0 0 10px 0; color: #003366 !important; font-size: 1.3rem; font-weight: 800; display: flex; align-items: center; gap: 10px; }
    .feature-card p { margin: 0; color: #64748b !important; font-size: 1rem; line-height: 1.6; }

    /* 💎 오른쪽 답변 구조 예시 (더욱 간결하고 세련되게) */
    .answer-structure {
        background-color: white !important;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        border: 1px solid #e2e8f0;
        position: sticky;
        top: 20px;
    }
    .answer-structure h3 { color: #001f3f !important; margin: 0 0 20px 0; font-size: 1.25rem; font-weight: 800; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px; }
    .answer-structure ul { list-style: none; padding: 0; margin: 0; }
    .answer-structure li { margin-bottom: 20px; }
    .answer-structure-title { font-weight: 800; color: #005691 !important; margin-bottom: 6px; display: flex; align-items: center; gap: 8px; font-size: 1.05rem;}
    .answer-structure-content { color: #475569 !important; font-size: 0.95rem; line-height: 1.6; background: #f8fafc; padding: 12px 15px; border-radius: 8px; border-left: 3px solid #cbd5e1;}

    /* 💎 플로팅 채팅 입력창 깔끔하게 유지 */
    div[data-testid="stChatInput"] { 
        position: sticky !important; 
        bottom: 0 !important; 
        padding: 20px 0 30px 0 !important; 
        background: linear-gradient(to top, #f8f9fa 80%, transparent) !important; 
        z-index: 1001 !important; 
    }
    div[data-testid="stChatInput"] > div { 
        background-color: #ffffff !important; 
        border: 2px solid #cbd5e1 !important; 
        border-radius: 30px !important; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stChatInput"] > div:focus-within { border-color: #005691 !important; }
    div[data-testid="stChatInput"] textarea { padding: 15px 20px !important; font-size: 1.05rem !important; }
    div[data-testid="stChatInput"] button { background-color: #001f3f !important; color: white !important; border-radius: 50% !important; padding: 8px !important; margin-right: 10px !important; }
    
    [data-testid="stChatMessage"] { 
        background-color: #ffffff; 
        border-radius: 16px; 
        padding: 20px 25px; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.03); 
        margin-bottom: 15px; 
        border: 1px solid #e9ecef; 
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

# 🗂️ [메인 UI] - 거짓말 메뉴 싹 지우고 정직하게 구성!
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): 
        st.image("검단탑병원-로고_고화질.png")
    st.markdown("---")
    st.markdown("### 📋 지원 기능 목록")
    st.markdown("- **🔍 지침서 AI 검색** (현재 데이터 기준)")
    st.markdown("- **🕵️‍♂️ 모의감독관 훈련** (실전 대비)")
    st.markdown("---")
    st.markdown("### 📢 시스템 상태")
    st.success("인증 지침서 DB 연동 완료")
    st.info("AI 추론 엔진 정상 가동 중")

logo_html = ""
if os.path.exists("검단탑병원-로고_고화질.png"):
    with open("검단탑병원-로고_고화질.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f"<img src='data:image/png;base64,{encoded_string}'>"

main_col, answer_col = st.columns([2.2, 1])

with main_col:
    # 모드 선택을 가장 위로 빼서 직관적으로 조작하게 함
    mode = st.radio("모드 선택", ["🔍 인증 지침서 검색", "🕵️‍♂️ 실전 모의감독관 훈련"], horizontal=True, label_visibility="collapsed")

    # 가짜 기능 지우고 진짜 기능 2개만 럭셔리하게 소개!
    st.markdown(f"""
    <div class='premium-welcome'>
        {logo_html}
        <div class='premium-welcome-text'>
            <h2>검단탑병원 인증조사 AI 도우미</h2>
            <p>방대한 인증 지침서를 단 몇 초 만에 검색하고,<br>AI 모의 감독관과 함께 실전 같은 면담 훈련을 진행하세요.</p>
        </div>
    </div>
    
    <div class='real-features-grid'>
        <div class='feature-card'>
            <h3>🔍 지침서 AI 검색</h3>
            <p>궁금한 인증 기준이나 절차를 아래 채팅창에 입력하세요. AI가 내부 지침서 원문을 분석하여 즉시 3단 양식으로 요약해 드립니다.</p>
        </div>
        <div class='feature-card'>
            <h3>🕵️‍♂️ 모의감독관 훈련</h3>
            <p>상단의 라디오 버튼을 변경하여 모의 훈련을 시작하세요. AI가 날카로운 질문을 던지고, 선생님의 답변을 지침에 맞게 채점해 줍니다.</p>
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
        st.info("💡 하단의 '새로운 질문 생성' 버튼을 눌러 모의 면담을 시작하세요.")
        if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
            with st.chat_message("assistant"):
                with st.spinner("💭 감독관이 지침서를 바탕으로 날카로운 질문을 준비 중입니다..."):
                    random_docs = vdb.similarity_search(random.choice(["지침", "규정"]), k=3)
                    sample_ctx = "\n".join([d.page_content for d in random_docs])
                    q_stream = get_intelligent_response(f"인증평가 감독관 질문 1개 생성. 행동 말고 규정 지식을 묻는 날카로운 질문을 하세요.\n내용:\n{sample_ctx}")
                    st.session_state.current_q = st.write_stream(q_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
        for m in st.session_state.train_msgs:
            with st.chat_message(m["role"]): st.markdown(m["content"])

with answer_col:
    # 디자인이 더 간결해진 우측 가이드
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
                <div class='answer-structure-content'>• 환자안전 지침서 3.4 낙상예방관리<br>• 5주기 인증기준 IPR.2.1</div>
            </li>
            <li>
                <div class='answer-structure-title'>📂 확인자료</div>
                <div class='answer-structure-content'>• 낙상 고위험 환자 평가 기록지<br>• 낙상 발생 보고서 및 RCA 분석<br>• 병동 환경 점검 체크리스트</div>
            </li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

if query := st.chat_input("인증 지침에 관해 질문하거나 감독관의 질문에 답변하십시오..."):
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        with st.chat_message("assistant"):
            with st.spinner("💭 지침서를 분석하여 표준 3단 양식으로 정리 중입니다..."):
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
                with st.spinner("💭 제출하신 답변을 지침서 기반으로 엄격하게 채점 중입니다..."):
                    try:
                        docs = vdb.similarity_search(st.session_state.current_q, k=8)
                        ctx_str = "\n\n".join([d.page_content for d in docs])
                        full_ans = st.write_stream(get_intelligent_response(f"감독관 시선 채점 및 보완. 출처 금지.\n질문: {st.session_state.current_q}\n답변: {query}\n데이터:\n{ctx_str}"))
                        st.session_state.train_msgs.append({"role": "assistant", "content": full_ans})
                        st.session_state.current_q = None
                    except Exception as e: st.error(f"🚨 오류: {e}")
