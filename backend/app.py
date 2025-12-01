# app_hf.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from llama_cpp import Llama
import faiss
import numpy as np
import pickle
import os
from dotenv import load_dotenv
import uvicorn

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

print("=" * 60)
print("모델 로딩 중...")
print("=" * 60)

# 1. 검색용 임베딩 모델
print("1/3 임베딩 모델 로딩...")
embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')

print("2/3 FAISS 인덱스 로딩...")
data_dir = os.path.join(PROJECT_ROOT, 'data')
index = faiss.read_index(os.path.join(data_dir, 'washing_machine.index'))

with open(os.path.join(data_dir, 'chunks.pkl'), 'rb') as f:
    chunks = pickle.load(f)

# 2. 답변 생성용 LLM (llama.cpp)
print("3/3 LLM 모델 로딩...")

# GGUF 모델 파일 경로
model_path = os.path.join(data_dir, 'models', 'A.X-4.0-Light-Q4_K_M.gguf')

if not os.path.exists(model_path):
    print(f"⚠️  모델 파일이 없습니다: {model_path}")
    print(f"   다음 경로에 모델을 다운로드해주세요:")
    print(f"   {os.path.dirname(model_path)}")
    print(f"   다운로드: https://huggingface.co/mykor/A.X-4.0-Light-gguf/blob/main/A.X-4.0-Light-Q4_K_M.gguf")
    llm_model = None
else:
    # llama.cpp로 모델 로드
    llm_model = Llama(
        model_path=model_path,
        n_ctx=2048,  # 컨텍스트 길이
        n_threads=4,  # CPU 스레드 수 (조정 가능)
        n_gpu_layers=0,  # CPU 전용 (GPU 있으면 숫자 증가)
        verbose=False
    )
    print(f"✅ 모델 로드 완료: A.X-4.0-Light")

print("=" * 60)
print("✅ 모든 모델 로딩 완료!")
print("=" * 60)

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
        "message": "세탁기 챗봇 API (A.X-4.0-Light)",
        "model": "A.X-4.0-Light-Q4_K_M",
        "model_loaded": llm_model is not None
    }

@app.post("/chat")
def chat(request: ChatRequest):
    try:
        if llm_model is None:
            return {
                "success": False,
                "error": "모델이 로드되지 않았습니다. 모델 파일을 다운로드해주세요."
            }
        
        print(f"\n질문: {request.query}")
        
        # 1. 벡터 검색
        query_embedding = embedding_model.encode([request.query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = index.search(query_embedding, 3)
        
        # 2. 컨텍스트 구성
        context = ""
        sources = []
        for idx in indices[0]:
            context += f"[페이지 {chunks[idx]['page']}]\n"
            context += chunks[idx]['content'][:300] + "\n\n"
            sources.append({
                "page": chunks[idx]['page'],
                "title": chunks[idx]['title']
            })
        
        # 3. 프롬프트 구성
        prompt = f"""당신은 삼성 세탁기 사용 설명서 전문 상담원입니다.
아래 매뉴얼을 참고하여 질문에 정확하고 친절하게 한국어로 답변하세요.

매뉴얼 내용:
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
        
        print(f"답변: {answer[:100]}...")
        print("답변 생성 완료")
        
        return {
            "success": True,
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        print(f"오류: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/search")
def search(request: SearchRequest):
    try:
        print(f"\n검색 요청: {request.query} (k={request.k})")
        
        # 1. 벡터 검색
        query_embedding = embedding_model.encode([request.query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = index.search(query_embedding, request.k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            # float32를 float로 변환하여 JSON 직렬화 가능하게 함
            score = float(distances[0][i])
            doc_idx = int(idx) # int64 -> int
            
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
    try:
        if llm_model is None:
            return {"success": False, "error": "모델이 로드되지 않았습니다."}
            
        print(f"\n생성 요청: {request.query}")
        print(f"선택된 문서 인덱스: {request.selected_indices}")
        
        # 1. 컨텍스트 구성
        context = ""
        sources = []
        
        for idx in request.selected_indices:
            # 인덱스 유효성 검사
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

        # 2. 프롬프트 구성
        prompt = f"""당신은 삼성 세탁기 사용 설명서 전문 상담원입니다.
아래 선택된 매뉴얼 내용을 바탕으로 질문에 정확하고 친절하게 한국어로 답변하세요.

매뉴얼 내용:
{context}

질문: {request.query}

답변:"""
        
        print("LLM 답변 생성 중...")
        
        # 3. LLM 답변 생성
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
        print(f"답변: {answer[:100]}...")
        
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