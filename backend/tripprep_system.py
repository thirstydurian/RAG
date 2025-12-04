import os
import asyncio
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

# --- 외부 라이브러리 ---
from anthropic import AsyncAnthropic
from tavily import TavilyClient
from pydantic import BaseModel, Field

# 환경 변수 로드
load_dotenv()

# API 키 설정
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# 클라이언트 설정
aclient = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# 모델 설정
FAST_MODEL = "claude-3-5-haiku-20241022"
SMART_MODEL = "claude-sonnet-4-5-20250929"

# --- Pydantic 데이터 모델 ---

class SearchResult(BaseModel):
    """검색 결과 데이터 구조"""
    query: str
    content: str
    sources: List[str]

class TripContext(BaseModel):
    """전체 워크플로우에서 공유되는 컨텍스트"""
    destination: str
    keywords: List[str]
    scout_data: List[SearchResult] = Field(default_factory=list)
    template: str = ""
    additional_data: List[SearchResult] = Field(default_factory=list)

    def get_combined_info(self) -> str:
        """모든 수집된 정보를 문자열로 반환 (출처 포함)"""
        text = "## Scout 정찰 정보\n"
        for item in self.scout_data:
            text += f"### Q: {item.query}\n{item.content}\n"
            if item.sources:
                text += f"**Sources:**\n" + "\n".join([f"- {s}" for s in item.sources]) + "\n\n"
        
        if self.additional_data:
            text += "## Writer 추가 리서치 정보\n"
            for item in self.additional_data:
                text += f"### Q: {item.query}\n{item.content}\n"
                if item.sources:
                    text += f"**Sources:**\n" + "\n".join([f"- {s}" for s in item.sources]) + "\n\n"
        return text

# --- 유틸리티 함수 ---

async def async_tavily_search(query: str, depth: str = "basic") -> SearchResult:
    """Tavily 검색을 비동기로 실행하는 래퍼 함수"""
    loop = asyncio.get_running_loop()
    
    def _search():
        try:
            return tavily_client.search(query=query, search_depth=depth, max_results=3)
        except Exception as e:
            return {"results": [], "error": str(e)}

    response = await loop.run_in_executor(None, _search)
    
    content_parts = []
    sources = []
    
    if 'results' in response:
        for res in response['results']:
            content_parts.append(f"- {res.get('content', '')}")
            sources.append(res.get('url', ''))
    
    return SearchResult(
        query=query,
        content="\n".join(content_parts) if content_parts else "검색 결과 없음",
        sources=sources
    )

# --- 에이전트 클래스 정의 ---

class ScoutAgent:
    """🕵️ Scout Agent: 병렬 검색 수행"""
    
    def __init__(self):
        self.name = "Scout Agent"

    async def run(self, ctx: TripContext) -> TripContext:
        print(f"[{self.name}] 정찰 시작: {ctx.destination}")
        
        queries = [
            (f"{ctx.destination} 입국 규정 비자 필수 요건 최신 2024 2025", "advanced"),
            (f"{ctx.destination} 여행 치안 주의사항 최신", "basic"),
        ]
        if ctx.keywords:
            queries.append((f"{ctx.destination} {ctx.keywords[0]} 추천 명소", "basic"))

        # 병렬 실행
        tasks = [async_tavily_search(q, d) for q, d in queries]
        results = await asyncio.gather(*tasks)

        ctx.scout_data = results
        print(f"[{self.name}] 정찰 완료: {len(results)}개 주제 수집")
        return ctx


class ArchitectAgent:
    """🏗️ Architect Agent: 동적 템플릿 설계"""

    def __init__(self):
        self.name = "Architect Agent"

    async def run(self, ctx: TripContext) -> TripContext:
        print(f"[{self.name}] 템플릿 설계 시작")

        scout_summary = ctx.get_combined_info()
        
        prompt = f"""
당신은 여행 보고서 설계자입니다.
수집된 정보를 바탕으로 '{ctx.destination}' 여행을 위한 최적의 목차(Template)를 작성하세요.

[수집된 정보]
{scout_summary}

[사용자 키워드]
{', '.join(ctx.keywords)}

[참고 항목 (Reference List)]
아래 항목들을 참고하여 목차를 구성하되, 반드시 모든 항목을 포함할 필요는 없습니다. 여행지의 특성과 수집된 정보에 맞춰 유연하게 구성하세요.
1. 필수 법적 요구사항 (비자, 여권, 거주지 등록 등)
2. 항공 (플랫폼, 저렴한 시기)
3. 숙박 (추천 지역)
4. 통신 (USIM, eSIM, 로밍)
5. 현지 결제 & 환전
6. 현지 교통수단
7. 필수 앱
8. 준비물
9. 주요 관광지 (미리 알면 좋은 정보, 역사적 의의, 가이드 설명, 포토 스팟)
10. 기념품, 특산물

[지침]
1. **중복 제거 (중요):** 목차 항목 간에 내용이 중복되지 않도록 구성하세요. 비슷한 내용은 하나의 섹션으로 통합하세요.
2. 일반적인 여행 정보 외에 수집된 정보의 '특이사항(경고, 필수요건)'을 상단에 배치하세요.
3. 사용자 키워드 관련 섹션을 구체적으로 만드세요.
4. 번호가 매겨진 목차 형식으로만 출력하세요. 설명은 필요 없습니다.
"""
        response = await aclient.messages.create(
            model=FAST_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        ctx.template = response.content[0].text
        print(f"[{self.name}] 템플릿 설계 완료")
        return ctx


class WriterAgent:
    """✍️ Writer Agent: Gap Analysis + 리포트 작성"""

    def __init__(self):
        self.name = "Writer Agent"

    async def run(self, ctx: TripContext) -> str:
        print(f"[{self.name}] 보고서 작성 시작")

        # 1. Gap Analysis
        gap_queries = await self._analyze_gaps(ctx)
        
        # 2. 추가 리서치
        if gap_queries:
            print(f"[{self.name}] 추가 리서치 필요: {len(gap_queries)}건")
            tasks = [async_tavily_search(q) for q in gap_queries]
            additional_results = await asyncio.gather(*tasks)
            ctx.additional_data = additional_results
        
        # 3. 최종 작성
        final_report = await self._write_final_report(ctx)
        return final_report

    async def _analyze_gaps(self, ctx: TripContext) -> List[str]:
        prompt = f"""
현재 우리는 '{ctx.destination}' 여행 보고서를 작성 중입니다.

[목차 (Template)]
{ctx.template}

[현재 보유 정보]
{ctx.get_combined_info()}

[지시사항]
1. 목차를 완성하기 위해 **절대적으로 부족한 정보**가 있는지 판단하세요.
2. 예를 들어, 목차에 '교통'이 있는데 보유 정보에 교통 정보가 없다면 검색이 필요합니다.
3. 최대 3개의 추가 검색 쿼리를 생성하세요.
4. 부족한 정보가 없다면 'NONE'이라고만 답하세요.
5. 출력 형식: JSON 포맷의 문자열 리스트 (예: ["도쿄 지하철 패스 가격", "도쿄 11월 날씨"])
"""
        response = await aclient.messages.create(
            model=FAST_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text.strip()
        if "NONE" in content:
            return []
        
        try:
            cleaned_json = content.replace("```json", "").replace("```", "").strip()
            queries = json.loads(cleaned_json)
            return queries if isinstance(queries, list) else []
        except:
            return []

    async def _write_final_report(self, ctx: TripContext) -> str:
        prompt = f"""
당신은 최고의 여행 전문 에디터입니다. 아래 정보를 종합하여 완벽한 여행 보고서를 작성하세요.

[여행지] {ctx.destination}
[키워드] {', '.join(ctx.keywords)}

[설계된 목차]
{ctx.template}

[모든 수집된 정보]
{ctx.get_combined_info()}

[작성 규칙]
1. 어조: 친절하고 전문적이며, 읽기 쉽게 작성하세요.
2. 형식: Markdown을 사용하고, 중요 정보는 볼드체나 리스트로 정리하세요.
3. **분량 조절(중요):** 각 섹션은 핵심만 간결하게 작성하고, 리스트 항목은 **최대 5개**로 제한하세요.
4. 정보가 없는 항목은 '정보를 찾을 수 없음'이라 적지 말고, 일반적인 팁으로 대체하세요.
5. **결론** 섹션에는 이 여행지의 매력을 한 줄로 요약하는 문구를 넣으세요.
6. 마지막에 면책 조항(정보의 시의성 등)을 작은 글씨로 추가하세요.
7. **출처 표기 (필수):** 본문 내용 중 Tavily 검색 결과의 URL을 활용하여 관련 정보 옆에 링크를 달아주세요. (예: [출처](URL))
8. **추천 제한:** 특정 숙박업소나 식당을 직접 추천하지 마세요. 대신 예약 플랫폼(Agoda, Booking.com 등)이나 식당 찾는 팁, 추천 지역 등을 안내하세요.
9. **체크박스 금지 (중요):** 보고서에 체크박스(☐, ☑, [ ], [x] 등)를 절대 사용하지 마세요. 일반 불릿 리스트(-)만 사용하세요.
"""
        response = await aclient.messages.create(
            model=SMART_MODEL,
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


class ChecklistAgent:
    """📋 Checklist Agent: 보고서에서 체크리스트 추출"""
    
    def __init__(self):
        self.name = "Checklist Agent"
    
    async def extract_checklist(self, report: str, destination: str) -> List[Dict]:
        """
        보고서에서 여행 준비 체크리스트 추출
        
        Returns:
            List[Dict]: [{"task": "...", "deadline": "...", "category": "..."}]
        """
        print(f"[{self.name}] 체크리스트 추출 시작")
        
        prompt = f"""
당신은 여행 준비 전문가입니다. 아래 '{destination}' 여행 보고서를 분석하여 여행 준비 체크리스트를 생성하세요.

[여행 보고서]
{report}

[지시사항]
1. 보고서 내용을 바탕으로 여행 전 준비해야 할 항목들을 추출하세요.
2. 각 항목에는 다음 정보를 포함하세요:
   - task: 해야 할 일 (구체적으로)
   - deadline: 마감 시기 (예: "출발 2주 전", "출발 3일 전", "출발 당일")
   - category: 카테고리 (예: "서류", "예약", "준비물", "금융", "통신", "건강")
3. 중요도 순으로 정렬하세요.
4. 최소 10개, 최대 20개 항목을 생성하세요.
5. 출력 형식: JSON 배열
   [
     {{"task": "여권 유효기간 확인 (6개월 이상)", "deadline": "출발 2개월 전", "category": "서류"}},
     {{"task": "항공권 예약", "deadline": "출발 1개월 전", "category": "예약"}}
   ]

**중요**: 반드시 유효한 JSON 형식으로만 출력하세요. 다른 설명은 포함하지 마세요.
"""
        
        response = await aclient.messages.create(
            model=FAST_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text.strip()
        
        try:
            # JSON 파싱
            cleaned_json = content.replace("```json", "").replace("```", "").strip()
            checklist = json.loads(cleaned_json)
            
            if not isinstance(checklist, list):
                return []
            
            print(f"[{self.name}] 체크리스트 추출 완료: {len(checklist)}개 항목")
            return checklist
            
        except Exception as e:
            print(f"[{self.name}] JSON 파싱 오류: {e}")
            return []


# --- 통합 시스템 클래스 ---

class TripPrepSystem:
    """TripPrep v2 로직을 캡슐화한 시스템 클래스"""
    
    def __init__(self):
        self.scout = ScoutAgent()
        self.architect = ArchitectAgent()
        self.writer = WriterAgent()
        self.checklist = ChecklistAgent()
        
        if not ANTHROPIC_API_KEY or not TAVILY_API_KEY:
            print("⚠️ Warning: API Key가 설정되지 않았습니다. .env 파일을 확인하세요.")

    async def generate_report(self, destination: str, keywords: List[str]) -> str:
        """보고서 생성 전체 파이프라인 실행"""
        try:
            # 컨텍스트 초기화
            ctx = TripContext(destination=destination, keywords=keywords)
            
            # 1. Scout
            ctx = await self.scout.run(ctx)
            
            # 2. Architect
            ctx = await self.architect.run(ctx)
            
            # 3. Writer
            final_report = await self.writer.run(ctx)
            
            return final_report
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"# 오류 발생\n\n보고서 생성 중 문제가 발생했습니다: {str(e)}"
