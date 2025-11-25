import PyPDF2

with open('Win10_Manual_KOR.pdf', 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

# 텍스트 파일로 저장
with open('extracted_text.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"총 {len(text)}자 추출 완료!")