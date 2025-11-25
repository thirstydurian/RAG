# search_test.py
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

# 1. 모델 로드
print("모델 및 데이터 로딩...")
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 2. FAISS 인덱스 로드
index = faiss.read_index('washing_machine.index')

# 3. 청크 메타데이터 로드
with open('chunks.pkl', 'rb') as f:
    chunks = pickle.load(f)

print(f"로드 완료! (총 {len(chunks)}개 청크)")

# 4. 검색 함수
def search(query, top_k=3):
    # 쿼리 임베딩
    query_embedding = model.encode([query])
    query_embedding = np.array(query_embedding).astype('float32')
    
    # 검색
    distances, indices = index.search(query_embedding, top_k)
    
    print(f"\n{'='*70}")
    print(f"질문: {query}")
    print('='*70)
    
    for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        chunk = chunks[idx]
        print(f"\n[{i+1}위] 거리: {dist:.2f} | 페이지: {chunk['page']} | 제목: {chunk['title']}")
        print("-"*70)
        print(chunk['content'][:300] + "...")
        print()

# 5. 테스트
if __name__ == "__main__":
    print("\n🔍 검색 테스트 시작\n")
    
    search("급수 호스 연결 방법")
    search("세탁기 에러 코드")
    search("건조 시 주의사항")
    search("세제 넣는 곳")
    
    # 인터랙티브 모드
    print("\n" + "="*70)
    print("직접 질문해보세요 (종료하려면 'quit' 입력)")
    print("="*70)
    
    while True:
        query = input("\n질문: ")
        if query.lower() in ['quit', 'exit', '종료']:
            print("종료합니다.")
            break
        if query.strip():
            search(query)