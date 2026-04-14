import streamlit as st
import requests

st.title("🔍 구글 API 계정 장부 털기 (ListModels)")

# 시크릿에서 키 가져오기
raw_keys = st.secrets.get("GOOGLE_API_KEYS", st.secrets.get("GOOGLE_API_KEY", []))
API_KEYS = [k.strip() for k in raw_keys.replace("[", "").replace("]", "").replace('"', '').replace("'", "").split(",") if k.strip()] if isinstance(raw_keys, str) else list(raw_keys)

if not API_KEYS:
    st.error("API 키가 없습니다.")
    st.stop()

api_key = API_KEYS[0]
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

st.write("📡 구글 서버에 선생님 계정의 전체 모델 목록을 요구하는 중...")

try:
    res = requests.get(url)
    data = res.json()
    
    if res.status_code != 200:
        st.error(f"목록 조회 실패: {data}")
    else:
        models = data.get('models', [])
        # 'embedContent' 기능을 지원하는 모델만 필터링
        embed_models = [m['name'] for m in models if 'embedContent' in m.get('supportedGenerationMethods', [])]
        
        if embed_models:
            st.success("✅ 찾았습니다! 선생님 계정에서 허락된 임베딩 모델 이름은 아래와 같습니다:")
            for m in embed_models:
                st.code(m)
            st.info("이 이름을 저에게 알려주시면, 그 이름으로 마스터 코드를 정확히 고정해 드리겠습니다.")
        else:
            st.error("🚨 [충격 결과] 선생님 계정(API 키)에는 '임베딩' 기능이 있는 모델이 단 하나도 할당되어 있지 않습니다!")
            st.write("즉, 코드가 문제가 아니라 구글 클라우드에서 선생님 프로젝트에 임베딩 기능 자체를 빼놓은 상태입니다.")
            
        with st.expander("구글이 보내온 전체 모델 장부 원본 보기"):
            st.json(data)
except Exception as e:
    st.error(f"오류 발생: {e}")
