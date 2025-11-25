# build_index.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

# 1. 청크 로드
print("청크 로딩...")
with open('chunks.pkl', 'rb') as f:
    chunks = pickle.load(f)

print(f"로드된 청크 개수: {len(chunks)}개")

# 2. 임베딩 모델 로드
print("\n임베딩 모델 로딩...")
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 3. 청크 내용만 추출
chunk_texts = [chunk['content'] for chunk in chunks]

# 4. 임베딩 생성
print("임베딩 생성 중...")
embeddings = model.encode(chunk_texts, show_progress_bar=True)
embeddings = np.array(embeddings).astype('float32')

print(f"임베딩 shape: {embeddings.shape}")

# 5. FAISS 인덱스 생성
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

print(f"FAISS 인덱스에 {index.ntotal}개의 벡터 추가 완료!")

# 6. 저장
faiss.write_index(index, 'washing_machine.index')

print("\n✅ 저장 완료!")
print("- washing_machine.index")