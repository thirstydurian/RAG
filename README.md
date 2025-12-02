# RAG 챗봇 (Retrieval-Augmented Generation Chatbot)

PDF 문서를 업로드하여 자동으로 벡터 인덱싱하고, 질문에 대해 관련 문서를 검색하여 AI 기반 답변을 생성하는 RAG 챗봇 시스템입니다.

## 주요 기능

### 🚀 핵심 기능
- **PDF 업로드 및 자동 처리**: UI에서 PDF를 업로드하면 자동으로 텍스트 추출, 청킹, 벡터 인덱싱 수행
- **인터랙티브 문서 검색**: 질문 시 Top-10 관련 문서를 검색하여 표시
- **선택적 컨텍스트 활용**: 검색된 문서 중 원하는 문서만 선택하여 답변 생성
- **마크다운 렌더링**: AI 답변을 마크다운 형식으로 표시
- **출처 추적**: 답변에 참고한 문서의 페이지 정보 표시
- **데이터 검사**: 인덱싱된 청크 목록 및 전체 텍스트 확인 가능

### 🎯 특별한 기능
- **중복 문자 자동 제거**: PDF 추출 시 발생하는 중복 문자 패턴 자동 정리 (예: "경경경제제제" → "경제")
- **토큰 기반 청킹**: 100 토큰 이하로 최적화된 청크 생성
- **한국어 최적화**: 한국어 임베딩 모델 및 SLM 사용

## 기술 스택

### Backend
- **프레임워크**: FastAPI 0.117.1
- **임베딩 모델**: jhgan/ko-sroberta-multitask (한국어 특화)
- **LLM**: A.X-4.0-Light-Q4_K_M.gguf (Gemma-2 기반, llama.cpp)
- **벡터 검색**: FAISS 1.8.0
- **PDF 처리**: pdfplumber
- **Python**: 3.9+

### Frontend
- **프레임워크**: React 19.2.0 + TypeScript
- **빌드 도구**: Vite 7.2.4
- **마크다운 렌더링**: react-markdown 10.1.0
- **Node.js**: 16+

## 프로젝트 구조

```
RAG/
├── backend/
│   ├── app.py              # FastAPI 메인 서버
│   ├── rag_pipeline.py     # PDF 처리 및 RAG 파이프라인
│   ├── requirements.txt    # Python 의존성
│   └── .env               # 환경 변수 (선택)
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # 메인 React 컴포넌트
│   │   └── App.css        # 스타일
│   ├── package.json       # Node.js 의존성
│   └── vite.config.ts     # Vite 설정
└── data/
    ├── models/            # LLM 모델 파일
    │   └── A.X-4.0-Light-Q4_K_M.gguf
    └── uploads/           # 업로드된 PDF 저장 (자동 생성)
```

## 설치 및 실행

### 1. 사전 준비

#### LLM 모델 다운로드
실행 전 반드시 LLM 모델을 다운로드하여 `data/models/` 경로에 위치시켜야 합니다.

```bash
# data/models 폴더 생성
mkdir -p data/models

# 모델 다운로드 (Hugging Face CLI 사용)
huggingface-cli download beomi/A.X-4.0-Light-GGUF A.X-4.0-Light-Q4_K_M.gguf --local-dir data/models
```

또는 [Hugging Face](https://huggingface.co/beomi/A.X-4.0-Light-GGUF)에서 직접 다운로드하여 `data/models/A.X-4.0-Light-Q4_K_M.gguf`에 저장하세요.

### 2. Backend 설치 및 실행

```bash
cd backend

# 가상환경 생성 (권장)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python app.py
```

Backend는 `http://localhost:8000`에서 실행됩니다.

### 3. Frontend 설치 및 실행

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

Frontend는 `http://localhost:3000`에서 실행됩니다.

## 사용 방법

### 기본 사용 흐름

1. **서버 시작**
   - Backend: `python app.py`
   - Frontend: `npm run dev`

2. **PDF 업로드**
   - 브라우저에서 `http://localhost:3000` 접속
   - "PDF 업로드" 탭으로 이동
   - PDF 파일 선택 후 "업로드 및 분석 시작" 클릭
   - 처리 완료 메시지 확인 (청크 개수 표시)

3. **질문하기**
   - "채팅" 탭으로 이동
   - 질문 입력 후 전송
   - Top-10 검색 결과가 표시됨
   - 원하는 문서를 선택/해제
   - "선택한 문서로 답변 생성" 클릭

4. **데이터 확인** (선택)
   - "데이터 확인" 탭에서 인덱싱된 청크 목록 확인
   - 전체 텍스트 미리보기 가능

## API 엔드포인트

### GET `/`
서버 상태 확인
```json
{
  "status": "ok",
  "message": "RAG 챗봇 API (A.X-4.0-Light)",
  "model": "A.X-4.0-Light-Q4_K_M",
  "model_loaded": true,
  "chunks_loaded": 77
}
```

### POST `/upload`
PDF 파일 업로드 및 처리
- **Request**: `multipart/form-data` (file)
- **Response**: 
```json
{
  "success": true,
  "message": "PDF 처리 완료",
  "filename": "example.pdf",
  "chunk_count": 77,
  "text_preview": "..."
}
```

### POST `/search`
문서 검색 (Top-K)
- **Request**: 
```json
{
  "query": "질문 내용",
  "k": 10
}
```
- **Response**: 
```json
{
  "success": true,
  "results": [
    {
      "index": 0,
      "page": 1,
      "title": "제목",
      "content": "내용...",
      "score": 0.85
    }
  ]
}
```

### POST `/generate`
선택된 문서로 답변 생성
- **Request**: 
```json
{
  "query": "질문 내용",
  "selected_indices": [0, 1, 2]
}
```
- **Response**: 
```json
{
  "success": true,
  "answer": "AI 답변...",
  "sources": [
    {"page": 1, "title": "제목"}
  ]
}
```

### GET `/data`
현재 로드된 데이터 정보
```json
{
  "text": "전체 텍스트...",
  "chunk_count": 77,
  "has_index": true
}
```

### GET `/chunks`
전체 청크 목록 조회
```json
{
  "success": true,
  "chunks": [...],
  "count": 77
}
```

## 데이터 처리 파이프라인

```
PDF 업로드 (UI)
    ↓
텍스트 추출 (pdfplumber)
    ↓ clean_text: 중복 문자 제거, 노이즈 제거
페이지별 텍스트
    ↓
청킹 (토큰 기반, 최대 100 토큰)
    ↓
임베딩 생성 (ko-sroberta-multitask)
    ↓
FAISS 인덱스 구축
    ↓
검색 및 답변 생성 (A.X-4.0-Light)
```

### 청킹 알고리즘
- 문장 단위로 분리
- 토큰 수가 100 이하가 되도록 문장을 그룹화
- 단일 문장이 100 토큰을 초과하는 경우 그대로 유지

### 텍스트 정제
- `(cid:숫자)` 패턴 제거
- `UUnnttiittlleedd` 패턴 제거
- 3회 이상 연속 반복 문자 제거 (예: "AAA" → "A")

## 주요 설정 값

### Backend (app.py)
- **검색 Top-K**: 기본 5 (SearchRequest), 채팅 시 5개 문서 사용
- **LLM 설정**:
  - `n_ctx`: 2048 (컨텍스트 길이)
  - `max_tokens`: 400 (답변 최대 길이)
  - `temperature`: 0.7
  - `top_p`: 0.9

### Frontend (App.tsx)
- **검색 Top-K**: 10 (사용자에게 10개 결과 표시)
- **API URL**: `http://localhost:8000`

## 문제 해결

### 모델 로딩 실패
```
⚠️ 모델 파일이 없습니다: data/models/A.X-4.0-Light-Q4_K_M.gguf
```
→ LLM 모델을 다운로드하여 `data/models/` 경로에 저장하세요.

### PDF 업로드 실패
→ `data/uploads/` 폴더가 자동 생성되지 않은 경우 수동으로 생성하세요.

### CORS 에러
→ Backend의 CORS 설정이 `allow_origins=["*"]`로 되어 있는지 확인하세요.

### 중복 문자 문제
→ `rag_pipeline.py`의 `clean_text` 함수가 자동으로 처리합니다. 새 PDF를 업로드하면 적용됩니다.

## 개발 정보

### 의존성 버전
- Python: 3.9+
- Node.js: 16+
- CUDA: 불필요 (CPU 전용)

### 주요 라이브러리
- `sentence-transformers`: 임베딩 생성
- `llama-cpp-python`: LLM 추론
- `faiss-cpu`: 벡터 검색
- `pdfplumber`: PDF 텍스트 추출
- `react-markdown`: 마크다운 렌더링

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.

## 기여

버그 리포트 및 기능 제안은 이슈로 등록해주세요.