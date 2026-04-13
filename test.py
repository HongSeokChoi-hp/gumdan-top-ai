import google.generativeai as genai
import time
import sys

# 1. 설정
genai.configure(api_key="AIzaSyAN0iPMwBCkzoJZm8Hn2FDyiHKePjVxx8s")
model = genai.GenerativeModel('gemini-2.5-flash')

# 파일 재사용 함수 (기존과 동일)
def get_or_upload(file_path, display_name):
    for f in genai.list_files():
        if f.display_name == display_name:
            return f
    new_file = genai.upload_file(path=file_path, display_name=display_name)
    while new_file.state.name == 'PROCESSING':
        time.sleep(2)
        new_file = genai.get_file(new_file.name)
    return new_file

f1 = get_or_upload("guide.pdf", "Main_Guide")
f2 = get_or_upload("manual2.pdf", "Sub_Manual")

# --- 한 글자씩 예쁘게 출력하는 함수 ---
def slow_type(text, speed=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed) # 여기서 출력 속도를 조절합니다!

print("\n🚀 검단탑병원 AI 인증마스터 입니다.")

while True:
    user_input = input("\n나: ")
    if user_input == '종료': break

    # 1. 즉시 반응 보여주기 (체감 속도 향상의 핵심!)
    print("\n[AI 마스터]: ", end="")
    slow_type("네, 질문하신 내용을 지침서에서 꼼꼼히 찾아보겠습니다. 잠시만 기다려주세요.\n", 0.02)
    
    prompt = f"지침서 내용을 바탕으로 전문적이고 정확하게 답변해줘: {user_input}"
    
    # 2. 실제 AI 답변 생성 시작
    response = model.generate_content([f1, f2, prompt], stream=True)
    
    print(">> ", end="")
    for chunk in response:
        if chunk.text:
            # AI가 뭉텅이로 준 데이터를 다시 한 글자씩 쪼개서 타이핑 효과를 줍니다.
            slow_type(chunk.text, 0.03) # 0.05로 올리면 더 천천히 씁니다.
            
    print("\n" + "-"*50)
