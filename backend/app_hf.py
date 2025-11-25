# app_hf.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer
import faiss
import numpy as np
import pickle
import torch

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
index = faiss.read_index('washing_machine.index')

with open('chunks.pkl', 'rb') as f:
    chunks = pickle.load(f)

# 2. 답변 생성용 LLM
print("3/3 Gemma 모델 로딩... (최초 1회만 다운로드)")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"   디바이스: {device}")

tokenizer = AutoTokenizer.from_pretrained("google/gemma-2-2b-it")

llm_model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-2-2b-it",
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    device_map="auto" if device == "cuda" else None
)

if device == "cpu":
    llm_model = llm_model.to("cpu")

print("=" * 60)
print("✅ 모든 모델 로딩 완료!")
print("=" * 60)

class ChatRequest(BaseModel):
    query: str

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "세탁기 챗봇 API (Hugging Face Gemma)",
        "device": device
    }

@app.post("/chat")
def chat(request: ChatRequest):
    try:
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
            context += chunks[idx]['content'][:500] + "\n\n"  # 길이 제한
            sources.append({
                "page": chunks[idx]['page'],
                "title": chunks[idx]['title']
            })
        
        # 3. 프롬프트 구성
        prompt = f"""당신은 삼성 세탁기 매뉴얼 전문가입니다.

매뉴얼 내용:
{context}

질문: {request.query}

위 매뉴얼 내용을 바탕으로 친절하게 답변하세요.
답변:"""
        
        print("LLM 답변 생성 중...")
        
        # 4. LLM 답변 생성
        inputs = tokenizer(prompt, return_tensors="pt").to(device)
        
        with torch.no_grad():
            outputs = llm_model.generate(
                **inputs,
                max_new_tokens=300,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id
            )
        
        answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # 프롬프트 제거
        answer = answer.replace(prompt, "").strip()
        
        print("답변 생성 완료")
        
        return {
            "success": True,
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        print(f"오류: {e}")
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)