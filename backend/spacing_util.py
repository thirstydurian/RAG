# 자동 띄어쓰기 추가 기능 (선택사항)
# PyKoSpacing을 사용하여 띄어쓰기 없는 한국어 텍스트에 자동으로 띄어쓰기 추가

"""
설치 방법:
pip install pykospacing

사용 방법:
rag_pipeline.py의 extract_text_from_pdf 함수에서
clean_text 함수 내부에 add_spacing 호출 추가
"""

from pykospacing import Spacing

def add_spacing_to_text(text):
    """
    띄어쓰기가 없는 한국어 텍스트에 자동으로 띄어쓰기 추가
    
    Args:
        text: 띄어쓰기가 없는 텍스트
        
    Returns:
        띄어쓰기가 추가된 텍스트
    """
    if not text or len(text.strip()) == 0:
        return text
    
    try:
        spacing = Spacing()
        # 긴 텍스트는 청크로 나눠서 처리 (메모리 효율)
        max_length = 500
        if len(text) > max_length:
            chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
            spaced_chunks = [spacing(chunk) for chunk in chunks]
            return ' '.join(spaced_chunks)
        else:
            return spacing(text)
    except Exception as e:
        print(f"띄어쓰기 추가 실패: {e}")
        return text  # 실패 시 원본 반환


# 테스트 예시
if __name__ == "__main__":
    # 띄어쓰기 없는 텍스트
    test_text = "시민들의오락을위해건설한곳이다.관중석계단의돌들은로마시민들이주워다집짓는데사용하고자부심을가졌다고하는데,지금은형체조차없다."
    
    print("원본 텍스트:")
    print(test_text)
    print("\n띄어쓰기 추가 후:")
    print(add_spacing_to_text(test_text))
