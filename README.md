# Intelligent RAG & TripPrep System 🌍

이 프로젝트는 **지능형 RAG 챗봇**과 **AI 여행 준비 리포트 생성기(TripPrep)**가 통합된 멀티 모달 AI 플랫폼입니다.

## 🌟 프로젝트 개요

두 가지 핵심 AI 서비스를 하나의 플랫폼에서 제공합니다:

1.  **RAG 챗봇 (Retrieval-Augmented Generation)**
    - PDF/TXT 문서를 업로드하고 대화하듯 질문하여 정확한 정보를 찾아내는 문서 분석 AI

2.  **TripPrep (AI Travel Report Generator)**
    - 여행 목적지와 키워드만 입력하면 멀티 에이전트가 협업하여 맞춤형 여행 가이드를 생성
    - 최신 웹 검색(Tavily)과 Notion 연동 지원

---

## 🚀 주요 기능

### 1. RAG 챗봇 (문서 분석)
- **다중 파일 처리**: PDF, TXT 파일을 동시에 여러 개 업로드 및 분석
- **텍스트 직접 입력**: 클립보드 텍스트를 바로 붙여넣어 분석 가능
- **정교한 전처리**:
    - 중복 문자 자동 제거 (예: "경경경제" → "경제")
    - 띄어쓰기 없는 한국어 텍스트도 문장 부호 기준으로 정확히 분리
- **인터랙티브 검색**: 질문 시 Top-K 관련 문서를 실시간으로 보여주고 선택 가능
- **투명한 출처**: 답변 생성에 사용된 문서의 페이지와 원문을 명확히 표시

### 2. TripPrep (여행 가이드)
- **맞춤형 리포트**: 목적지와 관심사(키워드)에 딱 맞는 여행 준비 리포트 생성
- **멀티 에이전트 시스템**:
    - **Scout**: Tavily API로 실시간 웹 검색 (비자, 날씨, 최신 정보)
    - **Architect**: 사용자 맞춤형 리포트 목차 설계
    - **Writer**: 수집된 정보를 바탕으로 고품질 마크다운 리포트 작성
- **Notion 연동**: 생성된 리포트와 체크리스트를 Notion 페이지로 자동 전송

---

## 🛠 기술 스택

### Backend
- **Framework**: FastAPI 0.117.1 (통합 서버)
- **LLM**:
    - **Local**: `A.X-4.0-Light-Q4_K_M.gguf` (RAG용, llama.cpp)
    - **Cloud**: Anthropic Claude 3.5 Haiku/Sonnet (TripPrep용)
- **Embedding**: `jhgan/ko-sroberta-multitask` (한국어 특화)
- **Vector Search**: FAISS (고속 유사도 검색)
- **Tools**: `pdfplumber` (PDF 처리), `Tavily API` (웹 검색)

### Frontend
- **Framework**: React 19.2.0 + TypeScript
- **Build**: Vite 7.2.4
- **UI**: 반응형 디자인, 다크 모드 지원
- **Rendering**: `react-markdown` (마크다운 렌더링)

---

## 📂 프로젝트 구조

```
finalproject/
├── RAG/
│   ├── backend/
│   │   ├── app.py              # FastAPI 메인 서버 (RAG + TripPrep 통합)
│   │   ├── rag_pipeline.py     # RAG 파이프라인 (PDF 처리, 임베딩)
│   │   ├── app_tripprep.py     # TripPrep 라우터 및 로직
│   │   ├── tripprep_system.py  # 멀티 에이전트 시스템 코어
│   │   └── requirements.txt    # 통합 의존성
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.tsx         # 메인 React 컴포넌트
│   │   │   └── components/     # UI 컴포넌트
│   └── data/
│       ├── models/             # 로컬 LLM 모델 저장소
│       └── uploads/            # 업로드된 문서 저장소
```

---

## ⚡ 설치 및 실행

### 1. 사전 준비

#### LLM 모델 다운로드 (RAG용)
```bash
# data/models/downloaded_models 폴더 생성
mkdir -p data/models/downloaded_models

# 모델 다운로드 (Hugging Face CLI)
huggingface-cli download beomi/A.X-4.0-Light-GGUF A.X-4.0-Light-Q4_K_M.gguf --local-dir data/models/downloaded_models
```

#### 환경 변수 설정 (.env)
`backend/.env` 파일을 생성하고 필요한 키를 입력하세요.
```env
# TripPrep용 (필수)
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
NOTION_TOKEN=secret_...
NOTION_DATABASE_ID=...
```

### 2. Backend 실행
```bash
cd backend

# 가상환경 활성화
python -m venv ../.venv
../.venv/Scripts/activate

# 의존성 설치
pip install -r requirements.txt

# 서버 시작
python app.py
```
Backend는 `http://localhost:8000`에서 실행됩니다.

### 3. Frontend 실행
```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 시작
npm run dev
```
Frontend는 `http://localhost:3000`에서 실행됩니다.

---

## 📡 API 엔드포인트

### 🤖 RAG Chatbot
| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/upload` | PDF/TXT 파일 업로드 및 텍스트 입력 처리 |
| `POST` | `/search` | 질문 관련 문서 Top-K 검색 |
| `POST` | `/generate` | 선택된 문서를 바탕으로 답변 생성 |
| `GET` | `/data` | 현재 로드된 데이터 현황 조회 |

### ✈️ TripPrep
| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/tripprep/generate` | 여행 리포트 생성 (목적지, 키워드) |
| `POST` | `/api/tripprep/notion/send-report` | 생성된 리포트를 Notion으로 전송 |
| `POST` | `/api/tripprep/notion/create-checklist` | 리포트 기반 체크리스트 Notion 생성 |

---

## 💡 사용 가이드

### RAG 챗봇 사용하기
1. **문서 업로드**: "PDF 업로드" 탭에서 파일 선택 또는 텍스트 붙여넣기 후 "분석 시작" 클릭
2. **질문하기**: "채팅" 탭에서 궁금한 점 질문 (예: "이 문서의 핵심 내용은?")
3. **답변 확인**: 검색된 문서 중 원하는 것을 선택하여 AI 답변 생성

### TripPrep 사용하기
1. **정보 입력**: 여행 가고 싶은 **목적지**(예: "오사카")와 **키워드**(예: "맛집, 쇼핑") 입력
2. **리포트 생성**: "가이드 생성" 버튼 클릭 (약 30~60초 소요)
3. **Notion 저장**: 결과 화면에서 "Notion에 저장" 버튼을 눌러 내 Notion으로 내보내기

---

## 📝 라이선스
이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.

Copyright (c) 2025 [서진주]