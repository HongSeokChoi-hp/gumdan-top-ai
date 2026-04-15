import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
import os
import random
import time
import base64

# ============================================================
# 🔑 Secrets 연동
# ============================================================
try:
    API_KEYS = list(st.secrets["GOOGLE_API_KEYS"])
except Exception:
    st.error("🚨 Streamlit Secrets에서 API 키를 찾을 수 없습니다.")
    st.stop()

SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증조사 AI 전문가", page_icon="🏅", layout="wide", initial_sidebar_state="auto")

# ============================================================
# 🎨 UI 고급화 CSS (유지)
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    .stApp { background-color: #F8FAFC !important; }
    p, span, div, li, h2, h3, h4 { color: #111827 !important; }
    
    [data-testid="stHeader"] { display: none !important; height: 0px !important; }
    #creatorBadge, .viewerBadge_container__1QSob, .stDeployButton { display: none !important; visibility: hidden !important; }
    
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; margin-top: 0px !important; }

    .enterprise-header { 
        background: linear-gradient(135deg, #002b5e 0%, #005691 100%); 
        padding: 10px 15px; 
        border-radius: 8px; 
        margin-top: 0px;
        margin-bottom: 5px;
        box-shadow: 0 4px 10px rgba(0, 86, 145, 0.1);
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .enterprise-header * { color: #ffffff !important; } 
    .enterprise-header h1 { margin: 0; font-size: 1.2rem !important; font-weight: 800; }
    .enterprise-header img { height: 24px !important; } 

    div[role="radiogroup"] {
        background-color: #e2e8f0;
        padding: 5px;
        border-radius: 12px;
        display: inline-flex;
        gap: 10px;
    }
    div[role="radiogroup"] label { margin: 0 !important; font-weight: 700 !important; }

    div[data-testid="stVerticalBlock"] > div:has(.enterprise-header) {
        position: sticky !important;
        top: 0 !important;
        z-index: 1000 !important;
        background-color: #F8FAFC !important; 
        padding-top: 15px !important;
    }
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        position: sticky !important;
        top: 70px !important; 
        z-index: 999 !important;
        background-color: #F8FAFC !important;
        padding-bottom: 10px !important;
        border-bottom: 1px solid #e2e8f0 !important; 
    }

    div[data-testid="stVerticalBlockOuter"] { min-height: 100dvh; display: flex; flex-direction: column; }
    div[data-testid="stVerticalBlock"] { flex-grow: 1 !important; }

    div[data-testid="stChatInput"] { 
        position: sticky !important; 
        bottom: 0 !important; 
        padding-bottom: 25px !important;
        padding-top: 15px !important;
        background-color: #F8FAFC !important; 
        z-index: 1001 !important; 
        margin-top: auto !important;
    }
    div[data-testid="stChatInput"] > div { border: 2px solid #005691 !important; border-radius: 20px !important; }
    
    [data-testid="stChatInput"] div[data-baseweb="textarea"], [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important; 
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important; 
    }

    [data-testid="stChatMessage"] { 
        background-color: #ffffff; 
        border-radius: 12px; 
        padding: 15px 20px; 
        box-shadow: 0 1px 4px rgba(0,0,0,0.05); 
        margin-bottom: 10px; 
        border: 1px solid #e2e8f0; 
    }
</style>
""", unsafe_allow_html=True)

# 🔐 로그인
if not st.session_state.get("authenticated", False):
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        st.markdown("<h3 style='text-align:center; color:#003366; font-weight:800; margin-bottom:20px;'>인증조사 AI 전문가</h3>", unsafe_allow_html=True)
        pwd = st.text_input("인증코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        elif pwd: st.error("❌ 인증 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🧠 검색 엔진 로드
# ============================================================
@st.cache_resource
def load_intelligent_db():
    if not os.path.exists("faiss_index_saved"): return None, "faiss_index_saved 폴더가 없습니다."
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=random.choice(API_KEYS))
        vdb = FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
        return vdb, None
    except Exception as e:
        return None, f"DB 로드 실패: {e}"

vdb, db_status_msg = load_intelligent_db()

if not vdb:
    st.error(f"🚨 엔진 로딩 실패: {db_status_msg}")
    st.stop()

def get_intelligent_response(prompt_text):
    time.sleep(1.6)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        google_api_key=random.choice(API_KEYS),
        temperature=0.0 # 🚨 [지능 롤백] 과부하 방지 및 팩트 최우선 
    )
    for chunk in llm.stream(prompt_text):
        if chunk.content:
            yield chunk.content

# ============================================================
# 🗂️ 메인 시스템 UI
# ============================================================
with st.sidebar:
    if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png")
    st.markdown("### 📡 시스템 상태")
    st.success("인증 지침서 동기화 완료 (100%)")
    if db_status_msg: st.warning(db_status_msg)

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

# 🚨 [핵심 변경] 출처 목록 강제 지시 프롬프트
SYS_RULE = """당신은 '검단탑병원 인증조사 AI 전문가'입니다.
[모드 2: 지침서 질문 (스마트 90% 일치 및 출처 명시 모드)]
1. 제공된 [원문 데이터]를 90% 이상 그대로 인용하여 답변하되, 깨진 글자(Ÿ, O 등)와 불규칙한 줄바꿈은 읽기 좋게 교정하십시오.
2. 문장 끝마다 [근거 1], [근거 2] 처럼 인용 표시를 하십시오.
3. **가장 중요:** 모든 답변이 끝난 후, 맨 아래에 반드시 **[📚 출처 목록]**을 작성하여 각 근거 번호가 어떤 문서(파일)에서 발췌되었는지 명확히 나열하십시오.
4. 원문 중 '핸드북(Handbook)'에 관련된 내용이 있다면 최우선으로 반영하십시오.
5. 제공된 데이터에 없는 내용은 절대 지어내지 마십시오."""

if mode == "🔍 인증 지침서 검색":
    for m in st.session_state.search_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

elif mode == "🕵️‍♂️ 실전 모의감독관 훈련":
    st.info("💡 모의 감독관이 무작위로 던지는 현장 질문에 답변하여 채점을 받아보세요.")
    if st.button("▶️ 새로운 감독관 질문 생성", use_container_width=True):
        with st.chat_message("assistant"):
            try:
                q_stream = get_intelligent_response("병원 인증평가 감독관이 현장 직원에게 던질법한 날카로운 질문 1개만 생성하시오. 인사말은 생략해.")
                st.session_state.current_q = st.write_stream(q_stream)
                st.session_state.train_msgs.append({"role": "assistant", "content": st.session_state.current_q})
            except Exception as e:
                st.error(f"🚨 질문 생성 오류: {e}")
                
    for m in st.session_state.train_msgs:
        with st.chat_message(m["role"]): st.markdown(m["content"])

placeholder_text = "규정 질문 또는 가볍게 인사를 건네보세요..." if mode == "🔍 인증 지침서 검색" else "감독관 질문에 답변하십시오..."

if query := st.chat_input(placeholder_text):
    if mode == "🔍 인증 지침서 검색":
        st.session_state.search_msgs.append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)
        with st.chat_message("assistant"):
            try:
                # 🚨 [지능 롤백] 너무 많은 문서를 줘서 멍청해지는 현상 방지 (k=5 복구)
                docs = vdb.similarity_search(query, k=5)
                
                # 🚨 [출처 해결] 문서의 실제 이름(metadata)을 추출하여 AI에게 함께 전달
                ctx_list = []
                for i, d in enumerate(docs):
                    src = d.metadata.get('source', '지침서 원문')
                    if isinstance(src, str):
                        src = src.split('/')[-1].split('\\')[-1] # 파일명만 깔끔하게 추출
                    ctx_list.append(f"[근거 {i+1} | 출처문서: {src}]\n{d.page_content}")
                ctx = "\n\n".join(ctx_list)
                
                res_stream = get_intelligent_response(f"{SYS_RULE}\n\n[원문 데이터]\n{ctx}\n\n사용자 입력: {query}")
                full_ans = st.write_stream(res_stream)
                st.session_state.search_msgs.append({"role": "assistant", "content": full_ans})
            except Exception as e:
                st.error(f"🚨 답변 생성 오류: {e}")
    else:
        if st.session_state.current_q:
            st.session_state.train_msgs.append({"role": "user", "content": query})
            with st.chat_message("user"): st.markdown(query)
            with st.chat_message("assistant"):
                try:
                    docs = vdb.similarity_search(st.session_state.current_q, k=4)
                    ctx_list = []
                    for i, d in enumerate(docs):
                        src = d.metadata.get('source', '지침서 원문')
                        if isinstance(src, str):
                            src = src.split('/')[-1].split('\\')[-1]
                        ctx_list.append(f"[근거 {i+1} | 출처문서: {src}]\n{d.page_content}")
                    ctx = "\n\n".join(ctx_list)
                    
                    eval_p = f"당신은 엄격한 인증평가 감독관입니다. 직원의 답변을 100점 만점으로 채점하고 보완 사항을 설명해줘. [원문] 내용을 바탕으로 답변하며, 답변 맨 밑에 [📚 출처 목록]을 반드시 작성해.\n\n질문: {st.session_state.current_q}\n직원 답변: {query}\n원문:\n{ctx}"
                    res_stream = get_intelligent_response(eval_p)
                    eval_ans = st.write_stream(res_stream)
                    st.session_state.train_msgs.append({"role": "assistant", "content": eval_ans})
                    st.session_state.current_q = None
                except Exception as e:
                    st.error(f"🚨 채점 오류: {e}")
        else:
            st.warning("먼저 '새로운 감독관 질문 생성' 버튼을 눌러주세요.")
