# app_hf.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
import faiss
import numpy as np
import pickle
import os
import shutil
from dotenv import load_dotenv
import uvicorn
import rag_pipeline

# 프로젝트 루트 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# .env 파일 로드
load_dotenv(os.path.join(BASE_DIR, '.env'))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
embedding_model = None
llm_model = None
index = None
chunks = []
current_pdf_text = ""

def initialize_models():
    global embedding_model, llm_model, index, chunks, current_pdf_text
    
    print("=" * 60)
    print("모델 로딩 중...")
    print("=" * 60)

    # 1. 검색용 임베딩 모델
    print("1/3 임베딩 모델 로딩...")
    embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

    # 2. 초기 데이터 로딩 (기존 데이터가 있다면)
    print("2/3 초기 데이터 로딩...")
    data_dir = os.path.join(PROJECT_ROOT, 'data')
    index_path = os.path.join(data_dir, 'washing_machine.index')
    chunks_path = os.path.join(data_dir, 'chunks.pkl')
    text_path = os.path.join(data_dir, 'extracted_text_pdfplumber.txt')

    if os.path.exists(index_path) and os.path.exists(chunks_path):
        try:
            index = faiss.read_index(index_path)
            with open(chunks_path, 'rb') as f:
                chunks = pickle.load(f)
            if os.path.exists(text_path):
                with open(text_path, 'r', encoding='utf-8') as f:
                    current_pdf_text = f.read()
            print(f"✅ 초기 데이터 로드 완료: {len(chunks)} chunks")
        except Exception as e:
            print(f"⚠️ 초기 데이터 로드 실패: {e}")
            index = None
            chunks = []

    # 3. 답변 생성용 LLM (llama.cpp)
    print("3/3 LLM 모델 로딩...")
    model_path = os.path.join(data_dir, 'models', 'A.X-4.0-Light-Q4_K_M.gguf')

    if not os.path.exists(model_path):
        print(f"⚠️  모델 파일이 없습니다: {model_path}")
        llm_model = None
    else:
        llm_model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_gpu_layers=0,
            verbose=False
        )
        print(f"✅ 모델 로드 완료: A.X-4.0-Light")

    print("=" * 60)
    print("✅ 모든 모델 로딩 완료!")
    print("=" * 60)

# 앱 시작 시 모델 초기화
initialize_models()

class ChatRequest(BaseModel):
    query: str

class SearchRequest(BaseModel):
    query: str
    k: int = 5

class GenerateRequest(BaseModel):
    query: str
    selected_indices: list[int]

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "RAG 챗봇 API (A.X-4.0-Light)",
        "model": "A.X-4.0-Light-Q4_K_M",
        "model_loaded": llm_model is not None,
        "chunks_loaded": len(chunks) if chunks else 0
    }

@app.post("/upload")
async def upload_pdf(
    files: list[UploadFile] = File(...),
    text_input: str = Form(None)
):
    global index, chunks, current_pdf_text
    
    try:
        upload_dir = os.path.join(PROJECT_ROOT, 'data', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        all_texts = []
        all_pages_content = []
        processed_files = []
        
        # Process uploaded files
        for file in files:
            if not file.filename:
                continue
                
            file_path = os.path.join(upload_dir, file.filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            print(f"파일 업로드 완료: {file.filename}")
            
            # Extract text based on file type
            if file.filename.lower().endswith('.pdf'):
                print(f"PDF 텍스트 추출 중: {file.filename}")
                text, pages = rag_pipeline.extract_text_from_pdf(file_path)
                all_texts.append(text)
                all_pages_content.extend(pages)
                processed_files.append(file.filename)
            elif file.filename.lower().endswith('.txt'):
                print(f"TXT 파일 읽기 중: {file.filename}")
                text, pages = rag_pipeline.extract_text_from_txt(file_path)
                all_texts.append(text)
                all_pages_content.extend(pages)
                processed_files.append(file.filename)
            else:
                print(f"지원하지 않는 파일 형식: {file.filename}")
        
        # Add text input if provided
        if text_input and text_input.strip():
            print("직접 입력된 텍스트 추가 중...")
            all_texts.append(text_input)
            all_pages_content.append({
                'page': len(all_pages_content) + 1,
                'text': text_input
            })
        
        # Check if we have any content
        if not all_texts:
            return {
                "success": False,
                "error": "처리할 파일이나 텍스트가 없습니다."
            }
        
        # Combine all texts
        combined_text = "\n\n=== 문서 구분 ===\n\n".join(all_texts)
        current_pdf_text = combined_text
        
        # 2. 청킹
        print("청킹 중...")
        new_chunks = rag_pipeline.chunk_text(all_pages_content, embedding_model)
        
        # 3. 인덱싱
        print("인덱싱 중...")
        new_index, _ = rag_pipeline.build_index(new_chunks, embedding_model)
        
        # 전역 변수 업데이트
        chunks = new_chunks
        index = new_index
        
        return {
            "success": True,
            "message": "문서 처리 완료",
            "file_count": len(processed_files),
            "files": processed_files,
            "has_text_input": bool(text_input and text_input.strip()),
            "chunk_count": len(chunks),
            "text_preview": combined_text[:1000] + "..." if len(combined_text) > 1000 else combined_text
        }
        
    except Exception as e:
        print(f"업로드 처리 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.get("/data")
def get_data():
    """현재 로드된 데이터 정보 반환"""
    return {
        "text": current_pdf_text,
        "chunk_count": len(chunks),
        "has_index": index is not None
    }

@app.get("/chunks")
def get_chunks():
    """전체 청크 목록 반환"""
    return {
        "success": True,
        "chunks": chunks,
        "count": len(chunks)
    }

@app.post("/chat")
def chat(request: ChatRequest):
    # 기존 로직 유지하되 index/chunks가 비어있을 때 처리 추가
    if not index or not chunks:
         return {"success": False, "error": "문서가 로드되지 않았습니다. PDF를 업로드해주세요."}
         
    try:
        if llm_model is None:
            return {"success": False, "error": "모델이 로드되지 않았습니다."}
        
        print(f"\n질문: {request.query}")
        
        # 1. 벡터 검색
        query_embedding = embedding_model.encode([request.query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = index.search(query_embedding, 5)
        
        # 2. 컨텍스트 구성
        context = ""
        sources = []
        for idx in indices[0]:
            if 0 <= idx < len(chunks):
                context += f"[페이지 {chunks[idx]['page']}]\n"
                context += chunks[idx]['content'][:300] + "\n\n"
                sources.append({
                    "page": chunks[idx]['page'],
                    "title": chunks[idx]['title']
                })
        
        # 3. 프롬프트 구성
        prompt = f"""당신은 문서 전문 상담원입니다.
아래 문서를 참고하여 질문에 정확하고 친절하게 한국어로 답변하세요.

문서 내용:
{context}

질문: {request.query}

답변:"""
        
        print("LLM 답변 생성 중...")
        
        # 4. LLM 답변 생성
        response = llm_model(
            prompt,
            max_tokens=400,
            temperature=0.7,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["질문:", "\n질문", "사용자:"],
            echo=False
        )
        
        answer = response['choices'][0]['text'].strip()
        
        return {
            "success": True,
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        print(f"오류: {e}")
        return {"success": False, "error": str(e)}

@app.post("/search")
def search(request: SearchRequest):
    if not index or not chunks:
         return {"success": False, "error": "문서가 로드되지 않았습니다. PDF를 업로드해주세요."}

    try:
        print(f"\n검색 요청: {request.query} (k={request.k})")
        
        query_embedding = embedding_model.encode([request.query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = index.search(query_embedding, request.k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(chunks):
                score = float(distances[0][i])
                doc_idx = int(idx)
                
                results.append({
                    "index": doc_idx,
                    "page": chunks[doc_idx]['page'],
                    "title": chunks[doc_idx]['title'],
                    "content": chunks[doc_idx]['content'],
                    "score": score
                })
            
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        print(f"검색 오류: {e}")
        return {"success": False, "error": str(e)}

@app.post("/generate")
def generate(request: GenerateRequest):
    if not chunks:
         return {"success": False, "error": "문서가 로드되지 않았습니다."}

    try:
        if llm_model is None:
            return {"success": False, "error": "모델이 로드되지 않았습니다."}
            
        print(f"\n생성 요청: {request.query}")
        
        context = ""
        sources = []
        
        for idx in request.selected_indices:
            if 0 <= idx < len(chunks):
                chunk = chunks[idx]
                context += f"[페이지 {chunk['page']}]\n"
                context += chunk['content'][:300] + "\n\n"
                sources.append({
                    "page": chunk['page'],
                    "title": chunk['title']
                })
        
        if not context:
            context = "참고할 문서가 선택되지 않았습니다."

        prompt = f"""당신은 문서 전문 상담원입니다.
아래 선택된 문서 내용을 바탕으로 질문에 정확하고 친절하게 한국어로 답변하세요.

문서 내용:
{context}

질문: {request.query}

답변:"""
        
        response = llm_model(
            prompt,
            max_tokens=400,
            temperature=0.7,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["질문:", "\n질문", "사용자:"],
            echo=False
        )
        
        answer = response['choices'][0]['text'].strip()
        
        return {
            "success": True,
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        print(f"생성 오류: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)