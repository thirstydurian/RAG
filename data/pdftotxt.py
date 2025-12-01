import pdfplumber
import re

def clean_text(text):
    """PDF에서 추출한 텍스트의 불필요한 패턴 제거"""
    if not text:
        return ""
    # (cid:숫자) 패턴 제거
    text = re.sub(r'\(cid:\d+\)', '', text)
    # UUnnttiittlleedd로 시작하는 푸터 라인 제거
    text = re.sub(r'UUnnttiittlleedd.*', '', text)
    return text

with pdfplumber.open('Washer.pdf') as pdf:
    text = ""
    for i, page in enumerate(pdf.pages):
        text += f"\n--- 페이지 {i+1} ---\n"
        raw_text = page.extract_text()
        text += clean_text(raw_text)
        
        # 표 추출
        tables = page.extract_tables()
        if tables:
            text += "\n[표 발견]\n"
            for table in tables:
                for row in table:
                    # 각 셀에도 clean_text 적용
                    cleaned_row = [clean_text(str(cell)) if cell else "" for cell in row]
                    text += " | ".join(cleaned_row)
                    text += "\n"
        
        text += "\n"

with open('extracted_text_pdfplumber.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"추출 완료! extracted_text_pdfplumber.txt 확인하세요")