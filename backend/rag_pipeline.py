import pdfplumber
import re
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def add_basic_spacing(text):
    """
    띄어쓰기가 없는 한국어 텍스트에 기본적인 띄어쓰기 추가
    주요 조사와 어미 패턴을 인식하여 단어 경계 추정
    """
    if not text or len(text.strip()) == 0:
        return text
    
    # 이미 띄어쓰기가 충분히 있는 경우 (전체 길이의 10% 이상이 공백)
    space_ratio = text.count(' ') / len(text) if len(text) > 0 else 0
    if space_ratio > 0.1:
        return text
    
    result = text
    
    # 1. 문장 부호 뒤에 띄어쓰기
    result = re.sub(r'([.!?])([가-힣A-Za-z0-9])', r'\1 \2', result)
    result = re.sub(r'([,;:])([가-힣A-Za-z0-9])', r'\1 \2', result)
    
    # 2. 한국어 조사 및 어미 패턴
    # 주격 조사: 이, 가
    result = re.sub(r'([가-힣])([이가])([가-힣])', lambda m: m.group(1) + m.group(2) + ' ' + m.group(3) if m.group(3) not in '가나다라마바사아자차카타파하' else m.group(0), result)
    
    # 목적격 조사: 을, 를
    result = re.sub(r'([가-힣])([을를])([가-힣])', lambda m: m.group(1) + m.group(2) + ' ' + m.group(3), result)
    
    # 관형격 조사: 의
    result = re.sub(r'([가-힣])의([가-힣])', r'\1의 \2', result)
    
    # 부사격 조사: 에, 에서, 에게, 로, 으로
    result = re.sub(r'([가-힣])(에서|에게|에도|에만|로서|으로)([가-힣])', r'\1\2 \3', result)
    result = re.sub(r'([가-힣])([에로])([가-힣])', lambda m: m.group(1) + m.group(2) + ' ' + m.group(3), result)
    
    # 접속 조사: 와, 과, 하고
    result = re.sub(r'([가-힣])(와|과|하고)([가-힣])', r'\1\2 \3', result)
    
    # 보조사: 은, 는, 도, 만, 까지
    result = re.sub(r'([가-힣])([은는도만])([가-힣])', lambda m: m.group(1) + m.group(2) + ' ' + m.group(3), result)
    result = re.sub(r'([가-힣])(까지)([가-힣])', r'\1\2 \3', result)
    
    # 3. 용언 어미
    # -다 (종결어미)
    result = re.sub(r'([가-힣])(다)([\.!?])', r'\1\2\3 ', result)
    result = re.sub(r'([가-힣])(했다|됐다|였다|이다)([\.!?,])', r'\1\2\3 ', result)
    
    # -고, -며, -면서 (연결어미)
    result = re.sub(r'([가-힣])(고|며|면서|지만|는데)([가-힣])', r'\1\2 \3', result)
    
    # -한, -된, -인 (관형사형 어미)
    result = re.sub(r'([가-힣])(한|된|인|은|를)([가-힣])', lambda m: m.group(1) + m.group(2) + ' ' + m.group(3) if len(m.group(1)) > 1 else m.group(0), result)
    
    # 4. 숫자와 한글 사이
    result = re.sub(r'([0-9])([가-힣])', r'\1 \2', result)
    result = re.sub(r'([가-힣])([0-9])', r'\1 \2', result)
    
    # 5. 영문자와 한글 사이
    result = re.sub(r'([A-Za-z])([가-힣])', r'\1 \2', result)
    result = re.sub(r'([가-힣])([A-Za-z])', r'\1 \2', result)
    
    # 6. 괄호 처리
    result = re.sub(r'([가-힣])(<|>|\(|\)|\[|\])([가-힣])', r'\1\2 \3', result)
    result = re.sub(r'(<|>|\(|\)|\[|\])([가-힣])', r'\1 \2', result)
    
    # 연속된 공백 제거
    result = re.sub(r'\s+', ' ', result)
    
    return result.strip()


def extract_text_from_pdf(pdf_path):
    """PDF에서 텍스트 추출"""
    def clean_text(text):
        if not text:
            return ""
        # Remove (cid:숫자) patterns
        text = re.sub(r'\(cid:\d+\)', '', text)
        # Remove UUnnttiittlleedd patterns
        text = re.sub(r'UUnnttiittlleedd.*', '', text)
        
        # Remove consecutive duplicate characters (e.g., "경경경" -> "경")
        # This pattern matches any character repeated 3 or more times consecutively
        def deduplicate_chars(match):
            return match.group(1)
        
        # Pattern: captures a character and matches if it repeats 2+ more times
        text = re.sub(r'(.)\1{2,}', deduplicate_chars, text)
        
        # 자동 띄어쓰기 추가 (비활성화: 규칙 기반 띄어쓰기가 오히려 품질 저하 가능)
        # text = add_basic_spacing(text)
        
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

def extract_text_from_txt(txt_path):
    """TXT 파일에서 텍스트 추출"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 페이지 개념이 없으므로 전체를 1페이지로 처리
    pages_content = [{
        'page': 1,
        'text': text
    }]
    
    return text, pages_content


def split_into_sentences(text):
    """
    간단한 문장 분리 (한국어/영어)
    . ! ? 뒤에서 분리 (띄어쓰기 없어도 처리 가능)
    """
    # 문장 종결 부호 뒤에서 분리 (공백 선택적)
    # 띄어쓰기가 없는 텍스트도 처리 가능하도록 \s*로 변경
    sentences = re.split(r'(?<=[.!?])\s*', text)
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
