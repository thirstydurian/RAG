import rag_pipeline

# PDF 텍스트 추출
text, pages = rag_pipeline.extract_text_from_pdf('../로마 한국어가이드.pdf')

print(f"총 페이지 수: {len(pages)}")
print("\n" + "="*60)
print("첫 페이지 텍스트 샘플 (처음 1000자):")
print("="*60)
print(pages[0]['text'][:1000])
print("\n" + "="*60)
print("두 번째 페이지 텍스트 샘플 (처음 1000자):")
print("="*60)
if len(pages) > 1:
    print(pages[1]['text'][:1000])
