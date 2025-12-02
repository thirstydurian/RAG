import sys
import os
from sentence_transformers import SentenceTransformer

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import rag_pipeline

def test_chunking():
    print("Testing chunking logic...")
    
    # Mock model with a simple tokenizer (length of words for simplicity in test?)
    # No, let's use the real model to be accurate
    model = SentenceTransformer('jhgan/ko-sroberta-multitask')
    
    # Test Case 1: Short sentences
    text1 = "안녕하세요. 반가워요. 이것은 테스트입니다."
    pages_content1 = [{'page': 1, 'text': text1}]
    
    chunks1 = rag_pipeline.chunk_text(pages_content1, model)
    print(f"Test 1 Chunks: {len(chunks1)}")
    for c in chunks1:
        print(f" - {c['content']} ({c['token_count']} tokens)")
        
    # Test Case 2: Long sentence (should be split if possible, but our logic keeps single sentence if > 100)
    # Let's create a very long sentence
    long_sentence = "이 문장은 매우 긴 문장입니다. " * 50
    pages_content2 = [{'page': 1, 'text': long_sentence}]
    
    chunks2 = rag_pipeline.chunk_text(pages_content2, model)
    print(f"\nTest 2 Chunks: {len(chunks2)}")
    for c in chunks2:
        print(f" - Length: {len(c['content'])} chars, Tokens: {c['token_count']}")
        
    # Test Case 3: Many sentences summing up to > 100 tokens
    many_sentences = "짧은 문장입니다. " * 50
    pages_content3 = [{'page': 1, 'text': many_sentences}]
    
    chunks3 = rag_pipeline.chunk_text(pages_content3, model)
    print(f"\nTest 3 Chunks: {len(chunks3)}")
    for c in chunks3:
        print(f" - Tokens: {c['token_count']}")
        assert c['token_count'] <= 100 or (c['token_count'] > 100 and c['content'].count('.') == 1)

if __name__ == "__main__":
    test_chunking()
