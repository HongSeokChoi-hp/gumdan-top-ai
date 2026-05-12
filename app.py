/* ============================================================ */
/* 📱 [모바일 UX] PC 기능 유지 + 모바일 전용 압축 레이아웃 */
/* ============================================================ */
@media (max-width: 768px) {

    /* 전체 라이트모드 강제 */
    html, body,
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stBottomBlock"],
    div[data-testid="stChatInputContainer"] {
        background-color: #f8f9fa !important;
        color: #111827 !important;
    }

    * {
        -webkit-text-size-adjust: 100% !important;
        box-sizing: border-box !important;
    }

    p, span, div, li, h1, h2, h3, h4, label {
        color: #111827 !important;
    }

    /* 모바일 전체 폭 압축 */
    .block-container {
        max-width: 100% !important;
        padding-top: 0.45rem !important;
        padding-left: 0.65rem !important;
        padding-right: 0.65rem !important;
        padding-bottom: 5.8rem !important;
        overflow-x: hidden !important;
    }

    /* Streamlit column 모바일 강제 세로 정렬 */
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
        display: block !important;
    }

    /* 기존 코드의 우측 가이드 숨김 무력화 */
    div[data-testid="column"]:nth-of-type(2) {
        display: block !important;
    }

    /* 컬럼 사이 간격 축소 */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.55rem !important;
    }

    /* 상단 병원 배너 - 모바일 compact */
    .dashboard-header {
        height: auto !important;
        min-height: 54px !important;
        padding: 10px 12px !important;
        margin-bottom: 8px !important;
        border-radius: 10px !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 10px !important;
    }

    .dashboard-header img {
        height: 30px !important;
        width: auto !important;
        padding: 3px !important;
        border-radius: 6px !important;
        flex-shrink: 0 !important;
    }

    .dashboard-header h1 {
        font-size: 1.05rem !important;
        line-height: 1.2 !important;
        margin: 0 !important;
        white-space: normal !important;
        word-break: keep-all !important;
        letter-spacing: -0.5px !important;
    }

    /* 모드 선택 박스 압축 */
    div[data-testid="stVerticalBlock"] > div:has(div[role="radiogroup"]) {
        padding: 7px 9px !important;
        margin-bottom: 8px !important;
        border-radius: 9px !important;
        background-color: #ffffff !important;
        border: 1px solid #dbe3ef !important;
    }

    div[role="radiogroup"] {
        gap: 4px !important;
        flex-wrap: nowrap !important;
    }

    div[role="radiogroup"] label {
        padding: 5px 6px !important;
        font-size: 0.72rem !important;
        line-height: 1.15 !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
    }

    /* 환영 섹션 - PC 내용 유지하되 높이 축소 */
    .welcome-section {
        padding: 12px 12px !important;
        margin-bottom: 9px !important;
        border-radius: 10px !important;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 10px !important;
        background-color: #ffffff !important;
    }

    .welcome-section img {
        height: 42px !important;
        width: auto !important;
        flex-shrink: 0 !important;
    }

    .welcome-section h2 {
        font-size: 0.98rem !important;
        line-height: 1.22 !important;
        margin: 0 0 4px 0 !important;
        word-break: keep-all !important;
    }

    .welcome-section p {
        font-size: 0.72rem !important;
        line-height: 1.35 !important;
        margin: 0 !important;
        word-break: keep-all !important;
    }

    .welcome-section br {
        display: none !important;
    }

    /* 추천 질문 제목 */
    .quick-prompts-title {
        font-size: 0.88rem !important;
        line-height: 1.2 !important;
        margin: 0 0 6px 0 !important;
        font-weight: 800 !important;
    }

    /* 추천 질문 버튼 - 한 화면에 최대한 들어오게 압축 */
    div[data-testid="stButton"] {
        margin-bottom: 4px !important;
    }

    div[data-testid="stButton"] button {
        min-height: 32px !important;
        height: 32px !important;
        padding: 5px 10px !important;
        border-radius: 16px !important;
        font-size: 0.72rem !important;
        line-height: 1.15 !important;
        font-weight: 700 !important;
        color: #005691 !important;
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
        justify-content: center !important;
        text-align: center !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    div[data-testid="stButton"] button:hover {
        transform: none !important;
        box-shadow: none !important;
    }

    /* 우측 AI 표준 답변 가이드 - 모바일에서도 보이게, compact 카드화 */
    .answer-structure {
        padding: 12px !important;
        margin-top: 6px !important;
        margin-bottom: 8px !important;
        border-radius: 10px !important;
        background-color: #ffffff !important;
        border: 1px solid #dbe3ef !important;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05) !important;
    }

    .answer-structure h3 {
        font-size: 0.92rem !important;
        line-height: 1.2 !important;
        margin: 0 0 8px 0 !important;
        padding-bottom: 7px !important;
        border-bottom: 1px solid #edf2f7 !important;
    }

    .answer-structure ul {
        display: grid !important;
        grid-template-columns: 1fr !important;
        gap: 6px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .answer-structure li {
        margin-bottom: 0 !important;
        padding: 9px 10px !important;
        border-radius: 9px !important;
        border-left: 4px solid #005691 !important;
        background-color: #f8fafc !important;
    }

    .answer-structure-title {
        font-size: 0.82rem !important;
        line-height: 1.2 !important;
        margin-bottom: 4px !important;
        font-weight: 800 !important;
        color: #005691 !important;
    }

    .answer-structure-content {
        font-size: 0.7rem !important;
        line-height: 1.35 !important;
        color: #475569 !important;
        word-break: keep-all !important;
    }

    .answer-structure-content br {
        display: none !important;
    }

    /* 채팅 메시지 영역 */
    div[data-testid="stChatMessage"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 8px !important;
        margin-bottom: 6px !important;
    }

    div[data-testid="stChatMessage"] p {
        font-size: 0.82rem !important;
        line-height: 1.45 !important;
        color: #111827 !important;
    }

    /* 하단 채팅창 - 흰색 바탕 + 검은 글씨 고정 */
    div[data-testid="stChatInput"] {
        max-width: 100% !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        padding: 8px 10px 12px 10px !important;
        background-color: #f8f9fa !important;
        border-top: 1px solid #e2e8f0 !important;
    }

    div[data-testid="stChatInput"] > div {
        margin: 0 !important;
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 16px !important;
        min-height: 44px !important;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.08) !important;
    }

    div[data-testid="stChatInput"] div[data-baseweb="base-input"],
    div[data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        font-size: 0.88rem !important;
        line-height: 1.3 !important;
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        -webkit-text-fill-color: #64748b !important;
        opacity: 1 !important;
    }

    div[data-testid="stChatInput"] button {
        background-color: #005691 !important;
        border-radius: 50% !important;
        width: 34px !important;
        height: 34px !important;
        min-width: 34px !important;
        margin-right: 4px !important;
        padding: 6px !important;
    }

    div[data-testid="stChatInput"] button svg {
        fill: #ffffff !important;
        color: #ffffff !important;
        width: 18px !important;
        height: 18px !important;
    }

    /* 모바일에서 불필요한 여백 제거 */
    .element-container {
        margin-bottom: 0.35rem !important;
    }

    hr {
        margin: 0.4rem 0 !important;
    }
}
