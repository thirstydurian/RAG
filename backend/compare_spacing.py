from sentence_transformers import SentenceTransformer
import numpy as np

# 임베딩 모델 로드
model = SentenceTransformer('jhgan/ko-sroberta-multitask')

# 테스트 텍스트
original_no_space = "시민들의오락을위해건설한곳이다.관중석계단의돌들은로마시민들이주워다집짓는데사용하고자부심을가졌다고하는데,지금은형체조차없다."

# 규칙 기반 띄어쓰기 적용 결과
with_auto_spacing = "시민들의 오락을 위해건설한곳이다. 관중석계단의 돌들은 로 마 시민들이 주워다집짓는 데사용하고 자부심을 가 졌다고 하는 데, 지금 은 형체조차없다."

# 올바른 띄어쓰기 (정답)
correct_spacing = "시민들의 오락을 위해 건설한 곳이다. 관중석 계단의 돌들은 로마 시민들이 주워다 집짓는데 사용하고자 부심을 가졌다고 하는데, 지금은 형체조차 없다."

# 검색 쿼리들
queries = [
    "로마 시민",
    "건설한 곳",
    "관중석 계단",
    "오락을 위해"
]

print("=" * 80)
print("임베딩 품질 비교 테스트")
print("=" * 80)

for query in queries:
    print(f"\n쿼리: '{query}'")
    print("-" * 80)
    
    # 각 버전의 임베딩 생성
    query_emb = model.encode([query])[0]
    no_space_emb = model.encode([original_no_space])[0]
    auto_space_emb = model.encode([with_auto_spacing])[0]
    correct_emb = model.encode([correct_spacing])[0]
    
    # 코사인 유사도 계산 (L2 정규화 후 내적)
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_no_space = cosine_similarity(query_emb, no_space_emb)
    sim_auto_space = cosine_similarity(query_emb, auto_space_emb)
    sim_correct = cosine_similarity(query_emb, correct_emb)
    
    print(f"  띄어쓰기 없음:     {sim_no_space:.4f}")
    print(f"  자동 띄어쓰기:     {sim_auto_space:.4f}")
    print(f"  올바른 띄어쓰기:   {sim_correct:.4f}")
    
    # 최고 점수 표시
    best = max(sim_no_space, sim_auto_space, sim_correct)
    if sim_no_space == best:
        print("  → 띄어쓰기 없음이 가장 좋음 ⚠️")
    elif sim_auto_space == best:
        print("  → 자동 띄어쓰기가 가장 좋음 ✅")
    else:
        print("  → 올바른 띄어쓰기가 가장 좋음 (기준)")

print("\n" + "=" * 80)
print("결론")
print("=" * 80)

# 토큰화 비교
print("\n[토큰화 비교]")
print(f"띄어쓰기 없음: {len(model.tokenizer.encode(original_no_space))} 토큰")
print(f"자동 띄어쓰기: {len(model.tokenizer.encode(with_auto_spacing))} 토큰")
print(f"올바른 띄어쓰기: {len(model.tokenizer.encode(correct_spacing))} 토큰")
