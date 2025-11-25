import pdfplumber

with pdfplumber.open('Washer.pdf') as pdf:
    text = ""
    for i, page in enumerate(pdf.pages):
        text += f"\n--- 페이지 {i+1} ---\n"
        text += page.extract_text()
        
        # 표 추출
        tables = page.extract_tables()
        if tables:
            text += "\n[표 발견]\n"
            for table in tables:
                for row in table:
                    text += " | ".join([str(cell) if cell else "" for cell in row])
                    text += "\n"
        
        text += "\n"

with open('extracted_text_pdfplumber.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"추출 완료! extracted_text_pdfplumber.txt 확인하세요")