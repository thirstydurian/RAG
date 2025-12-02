import pdfplumber
import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def extract_text_from_pdf(pdf_path):
    """PDF에서 텍스트 추출"""
    def clean_text(text):
        if not text:
            return ""
        text = re.sub(r'\(cid:\d+\)', '', text)
        text = re.sub(r'UUnnttiittlleedd.*', '', text)
        return text

    full_text = ""
    pages_content = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = ""
            raw_text = page.extract_text()
            page_text += clean_text(raw_text)
            
            tables = page.extract_tables()
            if tables:
                page_text += "\n[표 발견]\n"
                for table in tables:
                    for row in table:
                        cleaned_row = [clean_text(str(cell)) if cell else "" for cell in row]
                        page_text += " | ".join(cleaned_row)
                        page_text += "\n"
            
            pages_content.append({
                'page': i + 1,
                'text': page_text
            })
            full_text += f"\n--- 페이지 {i+1} ---\n{page_text}\n"
            
    return full_text, pages_content

def split_into_sentences(text):
    """
    간단한 문장 분리 (한국어/영어)
    . ! ? 뒤에 공백이나 줄바꿈이 오면 분리
    """
    # 문장 종결 부호 뒤에 공백이 있거나 줄바꿈이 있는 경우 분리
    # 예외 처리가 완벽하진 않지만 기본적인 문장 분리 수행
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def chunk_text(pages_content, tokenizer_model):
    """
    새로운 청킹 알고리즘:
    n 문장의 총 토큰수가 100이하인 최대 n
    단, n이 1인데도 100 토큰을 초과하는 경우 n=1로 한다.
    """
    chunks = []
    chunk_id = 0
    
    for page_data in pages_content:
        page_num = page_data['page']
        text = page_data['text']
        
        sentences = split_into_sentences(text)
        if not sentences:
            continue
            
        current_chunk_sentences = []
        current_tokens = 0
        
        for sentence in sentences:
            # 토큰 수 계산 (tokenizer_model.tokenizer.encode는 list 반환)
            # len(tokenizer_model.tokenizer.encode(sentence))가 정확한 토큰 수
            sentence_token_count = len(tokenizer_model.tokenizer.encode(sentence, add_special_tokens=False))
            
            # 1. 현재 문장 하나만으로도 100토큰이 넘는 경우
            if sentence_token_count > 100:
                # 만약 이전에 모아둔 문장들이 있다면 먼저 저장
                if current_chunk_sentences:
                    chunk_content = " ".join(current_chunk_sentences)
                    chunks.append({
                        'id': chunk_id,
                        'page': page_num,
                        'title': chunk_content[:50], # 제목은 첫 부분으로 대체
                        'content': chunk_content,
                        'token_count': current_tokens
                    })
                    chunk_id += 1
                    current_chunk_sentences = []
                    current_tokens = 0
                
                # 긴 문장 하나를 독립된 청크로 저장 (규칙: n=1인데도 100초과시 n=1)
                chunks.append({
                    'id': chunk_id,
                    'page': page_num,
                    'title': sentence[:50],
                    'content': sentence,
                    'token_count': sentence_token_count
                })
                chunk_id += 1
                continue
            
            # 2. 현재 문장을 추가했을 때 100토큰을 넘는지 확인
            if current_tokens + sentence_token_count > 100:
                # 넘으면 지금까지 모은 것을 저장
                chunk_content = " ".join(current_chunk_sentences)
                chunks.append({
                    'id': chunk_id,
                    'page': page_num,
                    'title': chunk_content[:50],
                    'content': chunk_content,
                    'token_count': current_tokens
                })
                chunk_id += 1
                
                # 현재 문장으로 새로운 청크 시작
                current_chunk_sentences = [sentence]
                current_tokens = sentence_token_count
            else:
                # 안 넘으면 추가
                current_chunk_sentences.append(sentence)
                current_tokens += sentence_token_count
        
        # 페이지의 마지막 남은 청크 저장
        if current_chunk_sentences:
            chunk_content = " ".join(current_chunk_sentences)
            chunks.append({
                'id': chunk_id,
                'page': page_num,
                'title': chunk_content[:50],
                'content': chunk_content,
                'token_count': current_tokens
            })
            chunk_id += 1
            
    return chunks

def build_index(chunks, model):
    """FAISS 인덱스 생성"""
    if not chunks:
        return None, None
        
    chunk_texts = [chunk['content'] for chunk in chunks]
    embeddings = model.encode(chunk_texts, show_progress_bar=False)
    embeddings = np.array(embeddings).astype('float32')
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    return index, embeddings
