import streamlit as st
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import random
import time

# ============================================================
# 🔑 [1, 5] API 키 로테이션 및 보안 인증 (0366)
# ============================================================
# 🚨 기획자님의 찐 API 키를 여기에 반드시 넣으세요!
API_KEYS = ["AIzaSyDYuAhAW3BAQvf4L6voyUdhk2m7X0e1p2U"] 
SET_PASSWORD = "0366" 

st.set_page_config(page_title="검단탑병원 인증 지능형 지식화", page_icon="🏅", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# 🎨 UI / 거머리 로고 차단
# ============================================================
st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #f8fafc; }
    
    /* 우측 하단 거머리 로고 완벽 차단 */
    .viewerBadge_container__1QSob, #viewerBadge, div[data-testid="stStatusWidget"], .stDeployButton { display: none !important; visibility: hidden !important; }
    footer { visibility: hidden; }

    /* 파란색 4px 테두리 */
    [data-testid="stChatInput"] { 
        border: 4px solid #005691 !important; 
        border-radius: 15px !important; 
    }

    .enterprise-header { background: linear-gradient(135deg, #003366 0%, #005691 100%); color: white; padding: 25px; border-radius: 15px; margin-bottom: 15px; }
    .enterprise-header h1 { margin: 0; font-size: 1.8rem; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

if not st.session_state.get("authenticated", False):
    st.write("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        if os.path.exists("검단탑병원-로고_고화질.png"): st.image("검단탑병원-로고_고화질.png", use_container_width=True)
        pwd = st.text_input("인증코드", type="password", placeholder="보안 코드를 입력하세요", label_visibility="collapsed")
        if pwd == SET_PASSWORD: st.session_state.authenticated = True; st.rerun()
        elif pwd: st.error("❌ 인증 코드가 일치하지 않습니다.")
    st.stop()

# ============================================================
# 🧠 [기획자님 지적 반영] 예외 처리 강화 & 듀얼 임베딩 로드
# ============================================================
@st.cache_resource
def load_intelligent_db():
    # 지적 2: faiss_index_saved 부재 시 확실한 에러 출력
    if not os.path.exists("faiss_index_saved"): 
        return None, "faiss_index_saved 폴더가 없습니다. 깃허브 업로드를 확인하세요."
