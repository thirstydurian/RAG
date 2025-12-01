# 프로젝트 소개
## 자동화된 RAG
기존 washer_rag 코드를 개선


# 세탁기 RAG 챗봇

가전제품(삼성 세탁기)의 매뉴얼을 벡터 DB로 저장하여 RAG 기반 챗봇을 구현합니다.


## 주요 구성 요소
- 한국어 임베딩 모델 : jhgan/ko-sroberta-multitask
- 한국어 SLM 모델 : A.X-4.0-Light-Q4_K_M.gguf
- 벡터 임베딩 유사성 검색 라이브러리 : FAISS

한국어 임베딩 모델, SLM 모델 -> '한글 임베딩/SLM 모델 순위, 리더보드' 같은 방식으로 웹 검색


## 주요 기능

- **벡터 검색**: FAISS를 이용한 빠른 문서 검색
- **LLM 기반 답변**: A.X-4.0-Light (Gemma-2 기반) 모델로 자연스러운 답변 생성
- **출처 추적**: 답변에 참고한 매뉴얼 페이지 표시
- **웹 UI**: React 기반의 모던한 채팅 인터페이스



## 데이터 처리 파이프라인

```
1. PDF
   ↓ (pdfplumber) : pdftotxt.py
2. extracted_text_pdfplumber.txt
   ↓ (chunking.py)
3. chunks.pkl (텍스트 청크들)
   ↓ (build_index.py)
4. washing_machine.index (FAISS 벡터 인덱스)
   ↓ (app.py)
5. 웹 UI에서 검색 및 답변 생성
```

## 프로젝트 구조

```
rag/
├── backend/           # FastAPI 백엔드
│   ├── app.py      # 메인 서버
│   └── requirements.txt
├── frontend/          # React 프론트엔드
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
└── data/              # 데이터 파일들
    ├── models/                # LLM 모델 파일 (A.X-4.0-Light-Q4_K_M.gguf)
    ├── washing_machine.index  # FAISS 벡터 인덱스
    └── chunks.pkl             # 문서 청크들
```

## 설치 방법

### 1. Backend 설치 및 실행

**필수: 모델 다운로드**
실행 전 반드시 LLM 모델을 다운로드하여 `backend/data/models/` 경로에 위치시켜야 합니다.
- **모델명**: A.X-4.0-Light-Q4_K_M.gguf
- **다운로드 경로**: `backend/data/models/A.X-4.0-Light-Q4_K_M.gguf`
- **다운로드 스크립트**:
  ```bash
  # data/models 폴더가 없다면 생성
  mkdir -p data/models
  
  # huggingface-cli 또는 파이썬 스크립트로 다운로드
  python data/models/downloadmodel.py
  ```

**환경 변수 설정 (.env)**
`backend/.env` 파일을 생성하고 다음 내용을 추가하세요:
```bash
# Hugging Face Hub 토큰 (모델 다운로드용)
HUGGINGFACE_HUB_TOKEN=your_token_here
```
- Hugging Face 토큰은 [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)에서 생성할 수 있습니다.
- 토큰이 없어도 공개 모델은 다운로드 가능하지만, 속도 제한이 있을 수 있습니다.

**패키지 설치:**
```bash
cd backend

# Python 3.9 이상 필요
# pip 패키지 설치
pip install -r requirements.txt

# 서버 실행
python app.py
```

**개별 설치 (requirements.txt 없을 경우):**
```bash
# FastAPI 및 서버
pip install fastapi==0.117.1 uvicorn[standard]==0.37.0 python-multipart==0.0.20

# 머신러닝/딥러닝
pip install torch==2.7.1 torchvision==0.22.1 transformers==4.45.0 sentence-transformers==3.0.1
pip install llama-cpp-python==0.2.90

# 벡터 검색
pip install faiss-cpu==1.8.0

# 데이터 처리
pip install numpy==1.26.4 pandas==2.3.2 scikit-learn==1.7.1

# 기타
pip install python-dotenv==1.0.0 pydantic==2.11.9 huggingface-hub>=0.23.2
```

Backend는 `http://localhost:8000` 에서 실행됩니다.

### 2. Frontend 설치 및 실행

```bash
cd frontend

# Node.js 16 이상 필요
# npm 패키지 설치
npm install

# 개발 서버 실행
npm run dev
```

Frontend는 `http://localhost:3000` 에서 실행됩니다.

## 사용 방법

1. Backend 터미널: `python app.py` 실행
2. Frontend 터미널: `npm run dev` 실행
3. 브라우저에서 `http://localhost:3000` 접속
4. 세탁기에 대한 질문 입력



## API 엔드포인트

- `GET /` - 서버 상태 확인
- `POST /chat` - 질문 입력 및 답변 생성
  - Request: `{"query": "질문 내용"}`
  - Response: `{"success": true, "answer": "답변", "sources": [...]}`


## 더 개선할 사항
- txt파일에 섞여있는 코드 등 불필요한 정보 자동으로 제거하는 코드 생성 필요 -> 완료
'''
(cid:2097)(cid:2074)(cid:3)(cid:801)(cid:2559)
(cid:1691)(cid:2627)(cid:3)(cid:2097)(cid:2074)(cid:3)(cid:910)(cid:1243)
(cid:1725)(cid:2593)(cid:801)
12 한국어
UUnnttiittlleedd--22 1122 22002255--0066--1100 (cid:31)(cid:31)(cid:31)(cid:31) 55::1177::0066
'''

- 현재 답변 생성 시간이 너무 긺. 약 2분 45초. -> SLM 모델 변경?
- 만든 챗봇의 확장성 생각해보기. 다른 메뉴얼을 넣어서 자동으로 처리할 수 있을지 등