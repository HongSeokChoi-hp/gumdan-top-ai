import streamlit as st
import google.generativeai as genai
import time
import os
import streamlit.components.v1 as components
from google.api_core.exceptions import ResourceExhausted

# ==========================================
# 🔐 보안 접속 세팅
# ==========================================
SET_PASSWORD = "0366" 
# ==========================================

st.set_page_config(page_title="검단탑병원 인증 AI", page_icon="🏅", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f0f2f5; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background-color: transparent !important;}
    .block-container { padding-top: 2rem; }
    .enterprise-header {
        background: linear-gradient(135deg, #003366 0%, #005691 100%);
        color: white; padding: 20px 30px; border-radius: 12px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 10px 20px rgba(0, 51, 102, 0.15);
        margin-bottom: 25px; border-left: 5px solid #8CC63F;
    }
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; font-weight: 800; color: white; letter-spacing: -0.5px; }
    .enterprise-header .sys-info { text-align: right; font-size: 0.85rem; opacity: 0.9; }
    .badge { background: #8CC63F; color: #003366; padding: 4px 10px; border-radius: 4px; font-weight: bold; margin-bottom:5px; display:inline-block;}
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: white; padding: 10px 20px 0px 20px; border-radius: 10px 10px 0 0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"] { height: 50px; font-size: 1.05rem; font-weight: 600; color: #555; }
    .stTabs [aria-selected="true"] { color: #005691 !important; border-bottom-color: #005691 !important; border-bottom-width: 3px !important; }
    .stChatMessage { border-radius: 10px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 15px;}
    [data-testid="stChatMessage"]:nth-child(even) { background-color: #f0f7ff; border: 1px solid #cce0ff; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: #ffffff; border: 1px solid #e1e4e8; }
</style>
""", unsafe_allow_html=True)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"):
            st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; margin:20px 0; font-weight:700;'>인증조사 마스터 AI 통합 시스템</h3>", unsafe_allow_html=True)
        pwd = st.text_input("보안 접근 코드를 입력하십시오.", type="password")
        if pwd == SET_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        elif pwd:
            st.error("⚠️ 인가되지 않은 코드입니다.")
    st.stop()

with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"):
        st.image("검단탑병원-로고_고화질.png", use_container_width=True)
    st.markdown("---")
    st.markdown("<div style='background:#f4f6f9; padding:15px; border-radius:8px; border:1px solid #e1e4e8;'>", unsafe_allow_html=True)
    st.markdown("🔒 **접속 등급:** 관리자 (1급)<br>📡 **서버 상태:** 최적화<br>📚 **지식 DB:**<br>• 2024 통합 지침서<br>• 급성기병원 표준지침서 Ver 5.0", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔄 시스템 메모리 정리", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    if st.button("🔒 안전 로그아웃", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("""
<div class='enterprise-header'>
    <div>
        <div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div>
        <h1>🏅 인증조사 마스터 AI</h1>
    </div>
    <div class='sys-info'>
        🟢 SYSTEM ONLINE<br>
        ⚡ LATENCY: 8ms<br>
        🛡️ ENCRYPTED SESSION
    </div>
</div>
""", unsafe_allow_html=True)

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction="너는 검단탑병원의 '인증조사 마스터 AI'야. 모든 답변은 한국어로만 해."
)

@st.cache_resource
def get_pdf():
    files = []
    existing = {f.display_name: f for f in genai.list_files()}
    for d, p in {"Guide_DB": "guide.pdf", "Manual_DB": "manual2.pdf"}.items():
        if d in existing: files.append(existing[d])
        else:
            f = genai.upload_file(path=p, display_name=d)
            while f.state.name == 'PROCESSING': time.sleep(0.5)
            files.append(genai.get_file(f.name))
    return files

pdf_files = get_pdf()

if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

timer_html = """
<div style="font-family:sans-serif; padding:15px; border-radius:8px; background-color:#fff3f3; border:1px solid #ffcaca; color:#d32f2f;">
    <h4 style="margin-top:0; margin-bottom:5px;">⚠️ 시스템 코어 냉각 중</h4>
    <p style="margin-top:0; font-size:14px;">데이터 처리량이 초과되었습니다. 60초 뒤 새로고침 하세요.</p>
    <div id="timer" style="font-size:1.3rem; font-weight:bold;">남은 시간: 60초</div>
</div>
<script>
    var timeLeft = 60;
    var elem = document.getElementById('timer');
    var timerId = setInterval(function() {
        if (timeLeft <= 0) {
            clearInterval(timerId);
            elem.innerHTML = "✅ 준비 완료! 페이지를 새로고침(F5) 해주세요.";
            elem.style.color = "#2e7d32";
        } else {
            elem.innerHTML = "⏳ 남은 시간: " + timeLeft + "초";
            timeLeft--;
        }
    }, 1000);
</script>
"""

tab1, tab2 = st.tabs(["🔍 통합 규정 검색 DB", "🕵️‍♂️ AI 감독관 실전 훈련"])

with tab1:
    st.info("💡 검색 속도 향상 및 과부하 방지를 위해 지침서를 하나씩 선택하여 검색합니다.")
    
    # [핵심 수정 1] 라디오 버튼으로 지침서 분리 선택 (데이터 무게 절반으로 감소)
    db_choice = st.radio("📚 검색할 지침서를 선택하세요:", ["2024 통합 지침서 (가이드북)", "급성기병원 표준지침서 Ver 5.0 (매뉴얼)"], horizontal=True)
    target_pdf = pdf_files[0] if "2024" in db_choice else pdf_files[1]
    
    chat_box1 = st.container(height=450)
    with chat_box1:
        for m in st.session_state.search_msgs:
            if m["role"] != "system_error":
                with st.chat_message(m["role"]): st.markdown(m["content"])
            else:
                components.html(timer_html, height=130)

    if prompt := st.chat_input("규정이나 지침을 입력하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": prompt})
        
        with chat_box1:
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                status_text = st.empty()
                status_text.markdown("🔄 **스캔 중...**")
                try:
                    # 선택된 1개의 PDF만 전송하여 토큰 낭비 방지
                    response = model.generate_content([target_pdf, f"질문:{prompt} (한국어로 답해)"], stream=True)
                    def stream_generator():
                        first_chunk = True
                        for chunk in response:
                            if first_chunk:
                                status_text.empty() 
                                first_chunk = False
                            if chunk.text: yield chunk.text
                                
                    full_response = st.write_stream(stream_generator)
                    st.session_state.search_msgs.append({"role": "assistant", "content": full_response})
                except ResourceExhausted:
                    status_text.empty()
                    components.html(timer_html, height=130)
                    st.session_state.search_msgs.append({"role": "system_error", "content": "error"})
                except Exception as e:
                    status_text.empty()
                    st.error(f"⚠️ 오류: {e}")

with tab2:
    st.info("💡 실전 훈련 모드입니다. 답변을 제출하면 즉시 채점 후 다음 질문이 이어집니다.")
    
    chat_box2 = st.container(height=450)
    with chat_box2:
        for m in st.session_state.train_msgs:
            if m["role"] != "system_error":
                with st.chat_message(m["role"]): st.markdown(m["content"])
            else:
                components.html(timer_html, height=130)
                
        if st.session_state.current_q is None:
            with st.chat_message("assistant"):
                status_text2 = st.empty()
                status_text2.markdown("🔄 **질문 생성 중...**")
                try:
                    res_q = model.generate_content([pdf_files[0], "인증평가 현장에서 직원에게 물어볼 짧은 규정 질문 1개만 해줘. 한국어로."], stream=True)
                    def stream_q():
                        first = True
                        for chunk in res_q:
                            if first:
                                status_text2.empty()
                                first = False
                            if chunk.text: yield chunk.text
                    q_text = st.write_stream(stream_q)
                    st.session_state.current_q = q_text
                    st.session_state.train_msgs.append({"role": "assistant", "content": q_text})
                except ResourceExhausted:
                    status_text2.empty()
                    components.html(timer_html, height=130)

    if train_prompt := st.chat_input("답변을 입력하십시오...", key="train_input"):
        st.session_state.train_msgs.append({"role": "user", "content": train_prompt})
        
        with chat_box2:
            with st.chat_message("user"): st.markdown(train_prompt)
            with st.chat_message("assistant"):
                status_text3 = st.empty()
                status_text3.markdown("🔄 **평가 중...**")
                try:
                    # [핵심 수정 2] 평가와 다음 질문 생성을 한 번의 요청으로 합침 (요청 횟수 1/2 감소)
                    combined_prompt = f"질문: '{st.session_state.current_q}'\n내 답변: '{train_prompt}'\n\n1. 이 답변을 지침서에 기반하여 한국어로 평가해줘.\n2. 평가가 끝나면 '---\n**[다음 질문]**\n' 이라는 구분선을 넣고, 직원에게 물어볼 새로운 인증평가 질문을 딱 1개만 해줘."
                    
                    res_eval = model.generate_content([pdf_files[0], combined_prompt], stream=True)
                    
                    def stream_eval():
                        first = True
                        for chunk in res_eval:
                            if first:
                                status_text3.empty()
                                first = False
                            if chunk.text: yield chunk.text
                            
                    eval_text = st.write_stream(stream_eval)
                    st.session_state.train_msgs.append({"role": "assistant", "content": eval_text})
                    
                    # 새로운 질문만 파싱해서 상태 저장 (다음번 평가를 위해)
                    if "[다음 질문]" in eval_text:
                        st.session_state.current_q = eval_text.split("[다음 질문]")[-1].strip()
                    else:
                        st.session_state.current_q = eval_text # 파싱 실패시 전체를 질문으로 간주
                        
                except ResourceExhausted:
                    status_text3.empty()
                    components.html(timer_html, height=130)
                    st.session_state.train_msgs.append({"role": "system_error", "content": "error"})
