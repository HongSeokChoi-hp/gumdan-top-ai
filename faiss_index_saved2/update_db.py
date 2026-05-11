import os
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 🚨 여기에 기획자님의 Gemini API 키를 직접 넣어주세요!
os.environ["GOOGLE_API_KEY"] = "AIzaSyDrcIHc88WwYqHK1mZ6clsKu500g_QjRhg"

def add_pdf_to_faiss(pdf_filename, db_folder="faiss_index_saved"):
    print(f"📖 [{pdf_filename}] 파일을 읽어옵니다...")
    
    # 1. PDF 읽기
    loader = PyPDFLoader(pdf_filename)
    documents = loader.load()

    # 2. AI가 소화하기 좋게 텍스트 쪼개기 (페이지 메타데이터 자동 보존됨)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(documents)
    print(f"✂️ 텍스트를 {len(splits)}개의 조각으로 나누었습니다.")

    # 3. 임베딩 모델 준비 (문장을 숫자로 변환)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    # 4. 기존 DB 불러오기
    print("🧠 기존 데이터베이스를 불러옵니다...")
    vdb = FAISS.load_local(db_folder, embeddings, allow_dangerous_deserialization=True)

    # 5. 기존 DB에 새로운 조각들 추가하기
    print("➕ 새로운 데이터를 DB에 주입합니다...")
    vdb.add_documents(splits)

    # 6. 업데이트된 DB 저장하기 (덮어쓰기)
    vdb.save_local(db_folder)
    print("🎉 완료! 데이터베이스가 성공적으로 업데이트되었습니다.")

# 실행: '핸드북.pdf' 라는 이름의 파일을 기존 DB에 추가합니다.
# 파일 이름이 다르면 아래 이름을 수정해주세요!
add_pdf_to_faiss("핸드북.pdf")