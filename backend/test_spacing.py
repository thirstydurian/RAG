import sys
sys.path.append('.')
from rag_pipeline import add_basic_spacing

# 테스트 텍스트 (띄어쓰기 없음)
test_texts = [
    "시민들의오락을위해건설한곳이다.관중석계단의돌들은로마시민들이주워다집짓는데사용하고자부심을가졌다고하는데,지금은형체조차없다.",
    "양쪽끝에나무가한그루씩서있으며대전차경기가열리면이나무들을열바퀴돌아야했다고한다.",
    "영화<냉정과열정사이>의촬영지이며<벤허>에서전차를몰고경주하는장면의모티프가된곳이다."
]

print("=" * 80)
print("자동 띄어쓰기 테스트")
print("=" * 80)

for i, text in enumerate(test_texts, 1):
    print(f"\n[테스트 {i}]")
    print(f"원본: {text}")
    spaced = add_basic_spacing(text)
    print(f"결과: {spaced}")
    print("-" * 80)
