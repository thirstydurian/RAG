# chunking.py
import re
import pickle

def washing_machine_chunking(text_file_path):
    """
    세탁기 매뉴얼 특화 청킹: 대제목/중제목 기준
    """
    with open(text_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    chunks = []
    chunk_id = 0
    
    # 페이지별로 분할
    pages = re.split(r'--- 페이지 \d+ ---', content)
    
    current_chunk = ""
    current_page = 1
    
    for page in pages:
        if not page.strip():
            continue
            
        # 빈 줄 2개 이상으로 섹션 구분
        sections = re.split(r'\n\n\n+', page)
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # 섹션이 제목으로 시작하는지 확인
            lines = section.split('\n')
            first_line = lines[0] if lines else ""
            
            # 제목 감지
            is_new_section = (
                len(first_line) < 30 and 
                not first_line.startswith('•') and
                not first_line.startswith('-') and
                len(lines) > 1
            )
            
            # 새 섹션이면 이전 chunk 저장
            if is_new_section and current_chunk and len(current_chunk) > 100:
                chunks.append({
                    'id': chunk_id,
                    'page': current_page,
                    'title': current_chunk.split('\n')[0][:50],
                    'content': current_chunk,
                    'char_count': len(current_chunk)
                })
                chunk_id += 1
                current_chunk = ""
            
            # 현재 섹션 추가
            if current_chunk:
                current_chunk += "\n\n" + section
            else:
                current_chunk = section
        
        current_page += 1
    
    # 마지막 chunk 저장
    if current_chunk.strip():
        chunks.append({
            'id': chunk_id,
            'page': current_page,
            'title': current_chunk.split('\n')[0][:50],
            'content': current_chunk,
            'char_count': len(current_chunk)
        })
    
    return chunks


if __name__ == "__main__":
    # 청킹 실행
    print("청킹 시작...")
    chunks = washing_machine_chunking('extracted_text_pdfplumber.txt')
    print(f"총 {len(chunks)}개의 chunk 생성")
    
    # 청크 저장
    with open('chunks.pkl', 'wb') as f:
        pickle.dump(chunks, f)
    
    print("✅ chunks.pkl 파일로 저장 완료!")
    
    # 샘플 출력
    print("\n=== 샘플 3개 ===")
    for chunk in chunks[:3]:
        print(f"\n[Chunk {chunk['id']}] 페이지 {chunk['page']}")
        print(f"제목: {chunk['title']}")
        print(f"길이: {chunk['char_count']}자")