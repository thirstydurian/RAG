import rag_pipeline

# 실제 PDF로 테스트
text, pages = rag_pipeline.extract_text_from_pdf('../로마 한국어가이드.pdf')

print(f"총 페이지 수: {len(pages)}")
print("\n" + "="*80)
print("첫 페이지 텍스트 (띄어쓰기 적용 후, 처음 1500자):")
print("="*80)
print(pages[0]['text'][:1500])
