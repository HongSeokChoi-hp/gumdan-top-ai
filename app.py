import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from PIL import Image

# ============================================================
# 🎨 1. 디자인 및 거머리 로고(배지) 완전 제거
# ============================================================
SET_PASSWORD = "0366" 
st.set_page_config(page_title="검단탑병원 인증 AI", page_icon="🏅", layout="wide")

st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    
    /* 🚫 스트림릿 기본 UI/로고/우측 하단 배지 완전 박멸 */
    header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"] {visibility: hidden; display: none !important;}
    div[data-testid="stStatusWidget"], .viewerBadge_container__1QSob, #viewerBadge {display: none !important;}
    
    .stApp { background-color: #f8fafc; }
    .enterprise-header { 
        background: linear-gradient(135deg, #003366 0%, #005691 100%); 
        color: white; padding: 30px; border-radius: 15px; margin-bottom: 20px;
    }
    .enterprise-header h1 { margin: 0; font-size: 2rem; color: white; font-weight: 900;}
</style>
""", unsafe_allow_html=True)

# [수정] 한글 파일명 로고를 안전하게 불러오는 함수 (이미지 없어도 앱 안죽음)
def load_logo_safely():
    logo_path = "검단탑병원-로고_고화질.png"
    try:
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            st.image(img, use_container_width=True)
        else:
            st.markdown("<h2 style='color:#003366; text-align:center;'>🏥 검단탑병원</h2>", unsafe_allow_html=True)
    except:
        st.markdown("<h2 style='color:#003366; text-align:center;'>🏥 검단탑병원</h2>", unsafe_allow_html=True)

# 🔐 로그인 
if not st.session_state.get("authenticated", False):
    st.write("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        load_logo_safely()
        pwd = st.text_input("보안코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        elif pwd: st.error("❌ 보안 코드가 틀립니다.")
    st.stop()

# ============================================================
# 🔑 2. 답변 엔진 (정상 모델명: gemini-1.5-flash)
# ============================================================
api_key = st.secrets.get("GOOGLE_API_KEY", "")
if not api_key: st.error("🚨 API 키 설정 확인 필요"); st.stop()

def get_answer(prompt_text):
    genai.configure(api_key=api_key)
    # [수정] 실존하는 가장 안정적인 모델명으로 고정
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"❌ AI 엔진 오류: {str(e)}"

# ============================================================
# 📚 3. 지식 로딩
# ============================================================
@st.cache_resource
def load_db():
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
        return FAISS.load_local("faiss_index_saved", embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None

vdb = load_db()

# ============================================================
# 🗂️ 4. 메인 화면
# ============================================================
st.markdown("<div class='enterprise-header'><h1>🏅 검단탑병원 인증조사 마스터</h1></div>", unsafe_allow_html=True)

if "msgs" not in st.session_state: st.session_state.msgs = []

chat_box = st.container(height=450)
for m in st.session_state.msgs:
    with chat_box.chat_message(m["role"]): st.markdown(m["content"])

if query := st.chat_input("질문을 입력하십시오..."):
    st.session_state.msgs.append({"role": "user", "content": query})
    with chat_box.chat_message("user"): st.markdown(query)
    
    with chat_box.chat_message("assistant"):
        with st.spinner("지침서를 정밀 분석 중..."):
            docs = vdb.similarity_search(query, k=4)
            ctx = "\n\n".join([d.page_content for d in docs])
            
            # [수정] 팩트 기반 답변 족쇄 프롬프트
            final_prompt = f"제공된 지침서 내용:\n{ctx}\n\n위 내용에 근거하여 다음 질문에 답하세요: {query}\n(자료에 없는 내용은 모른다고 답할 것)"
            
            ans = get_answer(final_prompt)
            st.markdown(ans)
            st.session_state.msgs.append({"role": "assistant", "content": ans})
