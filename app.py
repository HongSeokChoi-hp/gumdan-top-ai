import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
import time

# [보안 설정]
SET_PASSWORD = "0366"
st.set_page_config(page_title="검단탑병원 진단 모드", layout="wide")

if not st.session_state.get("authenticated", False):
    pwd = st.sidebar.text_input("보안 코드", type="password")
    if pwd == SET_PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# [API 키 로드]
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [raw_keys] if isinstance(raw_keys, str) else list(raw_keys)

# ==========================================
# 🔍 긴급 진단 엔진 (범인을 찾아냅니다)
# ==========================================
def diagnostic_check():
    if not API_KEYS:
        return "❌ 시크릿 박스에 API 키가 하나도 없습니다."
    
    key = API_KEYS[0]
    try:
        # 1. 임베딩 모델 테스트
        st.write(f"📡 현재 시도 중인 키: `{key[:10]}...` (앞부분 일부)")
        genai.configure(api_key=key)
        
        # 실제 구글 서버에 찔러보기
        temp_emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=key)
        temp_emb.embed_query("test")
        return "✅ 성공! 이제 정상 작동해야 합니다."
    except Exception as e:
        # [핵심] 여기서 구글이 보내는 진짜 에러를 잡아냅니다.
        return f"🚨 [진짜 에러 발생] : {str(e)}"

st.title("🏅 검단탑병원 AI 시스템 진단")
result = diagnostic_check()

if "🚨" in result:
    st.error(result)
    st.markdown("---")
    st.warning("위의 빨간색 에러 메시지(영어 포함)를 캡처하거나 복사해서 저에게 보내주세요!")
else:
    st.success(result)
    st.info("성공 메시지가 뜬다면 다시 원래의 정식 코드를 넣으시면 됩니다.")
