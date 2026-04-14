import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import random

# ============================================================
# 🎨 1. [디자인/보안] 병원 전용 프리미엄 UI & 안전한 로고 삭제
# ============================================================
SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증 AI 마스터", page_icon="🏅", layout="wide", initial_sidebar_state="collapsed")

# [핵심] 화면 백지화 에러를 일으킨 폭탄 코드를 빼고 안전하게 잡다한 UI만 지웁니다.
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 🚫 스트림릿 툴바, 헤더, 푸터 안전하게 삭제 */
    #MainMenu, header, footer {visibility: hidden !important; display: none !important;}
    [data-testid="stToolbar"], [data-testid="stDecoration"] {display: none !important;}
    a[href*="streamlit.io"] {display: none !important;}
    iframe {display: none !important;}
    
    .block-container {padding-top: 1rem !important; padding-bottom: 1rem !important;}

    /* 🖥️ PC & 모바일 공통 디자인 */
    .enterprise-header { 
        background: linear-gradient(135deg, #003366 0%, #005691 100%); 
        color: white; padding: 30px 40px; border-radius: 15px; 
        margin-bottom: 20px; box-shadow: 0 10px 30px rgba(0, 51, 145, 0.2); 
    }
    .badge { 
        background: #8CC63F; color: #003366; padding: 6px 14px; 
        border-radius: 6px; font-weight: bold; margin-bottom: 10px; display: inline-block; font-size: 0.9rem; 
    }
    .enterprise-header h1 { margin: 0; font-size: 2.2rem; font-weight: 900; color: white; letter-spacing: -1px; }
    
    [data-testid="stChatInput"] { 
        border: 3px solid #005691 !important; border-radius: 15px !important; 
        box-shadow: 0 10px 30px rgba(0, 86, 145, 0.2) !important; 
        background-color: white !important; padding: 10px !important; 
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #f1f5f9; border-radius: 10px 10px 0 0; 
        padding: 0 20px; font-weight: 800; color: #64748b; font-size: 1.1rem; 
    }
    .stTabs [aria-selected="true"] { background-color: #005691 !important; color: white !important; }

    /* 📱 모바일 최적화 */
    @media (max-width: 768px) {
        .enterprise-header { padding: 20px !important; margin-bottom: 15px !important;}
        .enterprise-header h1 { font-size: 1.8rem !important; line-height: 1.2 !important; word-break: keep-all !important;}
        .badge { font-size: 0.8rem !important; padding: 5px 10px !important; margin-bottom: 10px !important;}
        .stTabs [data-baseweb="tab"] { font-size: 1rem !important; padding: 0 10px !important;}
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("authenticated", False):
    st.write("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        # [수정] 에러를 일으킨 옛날 명령어(use_column_width)를 최신(use_container_width)으로 바꿨습니다!
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; font-weight:800; color:#003366; margin-top:20px;'>인증 AI 마스터 접속</h3>", unsafe_allow_html=True)
        pwd = st.text_input("보안코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        else:
            if pwd: st.error("❌ 보안 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🔑 2. 모바일 먹통 방지용 "통짜 출력" 엔진 (타이핑 효과 삭제)
# ============================================================
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

if not API_KEYS: st.error("🚨 설정된 API 키가 없습니다."); st.stop()

def generate_with_retry(prompt_text):
    keys = list(API_KEYS)
    random.shuffle(keys)
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            # stream=False로 설정하여 모바일 통신 끊김 원천 차단
            response = model.generate_content(prompt_text, stream=False)
            return response.text
        except Exception: continue
    raise Exception("모든 AI 엔진이 응답하지 않습니다. 잠시 후 다시 시도해주세요.")

# ============================================================
# 📚 3. 0초 로딩 
# ============================================================
@st.cache_resource
def load_vdb():
    if not os.path.exists("faiss_index_saved"):
        return None, "🚨 서버에 'faiss_index_saved' 지식 폴더가 없습니다."
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=API_KEYS[0])
        return FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True), None
    except Exception as e:
        return None, f"지식 데이터 연결 실패: {str(e)}"

st.markdown("<div class='enterprise-header'><div class='badge'>GUMDAN TOP HOSPITAL AI CORE</div><h1>🏅 인증조사 마스터 AI</h1></div>", unsafe_allow_html=True)

vdb, error_msg = load_vdb()
if error_msg: st.error(error_msg); st.stop()

# ============================================================
# 🗂️ 4. 통합 규정 검색 및 훈련 
# ============================================================
if "search_msgs" not in st.session_state: st.session_state.search_msgs = []
if "train_msgs" not in st.session_state: st.session_state.train_msgs = []
if "current_q" not in st.session_state: st.session_state.current_q = None

SYSTEM_PROMPT = """당신은 검단탑병원의 최고 등급 인증평가 전문 컨설턴트입니다.
아래 제공된 [지침서 내용]만을 바탕으로 답변하되, 다음 규칙을 엄격히 지키세요:
1. 문서의 내용을 기계적으로 복사/붙여넣기 하지 마세요.
2. 동일한 목차나 내용이 반복될 경우, 하나로 깔끔하게 합쳐서 사람이 읽기 쉬운 자연스러운 문장으로 요약하세요.
3. 전문적이고 정중한 한국어로 답변하며, 답변 끝에 반드시 핵심 근거를 부드럽게 요약하여 덧붙이세요.
"""

tab1, tab2 = st.tabs(["🔍 통합 규정 검색", "🕵️‍♂️ AI 감독관 훈련"])

with tab1:
    chat_box1 = st.container(height=350)
    for m in st.session_state.search_msgs:
        with chat_box1.chat_message(m["role"]): st.markdown(m["content"])

    if query := st.chat_input("규정이나 지침에 대해 질문하십시오...", key="search_input"):
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with chat_box1.chat_message("user"): st.markdown(query)
        
        with chat_box1.chat_message("assistant"):
            with st.spinner("지침서를 분석 중입니다. 잠시만 기다려주세요..."):
                try:
                    docs = vdb.similarity_search(query, k=4)
                    context_data = "\n\n".join([d.page_content for d in docs])
                    smart_prompt = f"{SYSTEM_PROMPT}\n\n[지침서 내용]\n{context_data}\n\n[사용자 질문]: {query}"
                    
                    full_res = generate_with_retry(smart_prompt)
                    st.markdown(full_res)
                    st.session_state.search_msgs.append({"role": "assistant", "content": full_res})
                except Exception as e:
                    st.error(f"⚠️ 시스템 지연입니다. 다시 시도해주세요.")

with tab2:
    chat_box2 = st.container(height=350)
    for m in st.session_state.train_msgs:
        with chat_box2.chat_message(m["role"]): st.markdown(m["content"])
    
    if st.button("▶️ 새로운 감독관 현장 질문 생성", use_container_width=True):
        st.session_state.current_q = "생성중"
        with chat_box2.chat_message("assistant"):
            with st.spinner("감독관 질문을 생성 중입니다..."):
                try:
                    full_q = generate_with_retry("병원 인증평가 감독관이 던질법한 짧은 현장 질문 하나 해줘.")
                    st.markdown(full_q)
                    st.session_state.current_q = full_q
                    st.session_state.train_msgs.append({"role": "assistant", "content": full_q})
                except:
                    st.error("⚠️ 질문 생성 실패.")

    if answer_input := st.chat_input("답변을 입력하십시오...", key="train_input"):
        if st.session_state.current_q and st.session_state.current_q != "생성중":
            st.session_state.train_msgs.append({"role": "user", "content": answer_input})
            with chat_box2.chat_message("user"): st.markdown(answer_input)
            with chat_box2.chat_message("assistant"):
                with st.spinner("답변을 채점 중입니다..."):
                    try:
                        docs = vdb.similarity_search(st.session_state.current_q, k=3)
                        ref_ctx = "\n\n".join([d.page_content for d in docs])
                        eval_p = f"{SYSTEM_PROMPT}\n\n[지침서 내용]\n{ref_ctx}\n\n[상황]: 감독관이 '{st.session_state.current_q}'라고 질문했고, 직원이 '{answer_input}'라고 답변했습니다. 지침서를 바탕으로 친절하게 채점하고 정답을 알려주세요."
                        
                        final_eval = generate_with_retry(eval_p)
                        st.markdown(final_eval)
                        st.session_state.train_msgs.append({"role": "assistant", "content": final_eval})
                        st.session_state.current_q = None 
                    except:
                        st.error("⚠️ 채점 엔진 오류.")
        else: st.warning("먼저 질문 생성 버튼을 눌러주십시오.")
