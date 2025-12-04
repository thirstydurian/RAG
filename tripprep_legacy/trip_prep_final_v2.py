import os
import asyncio
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

# --- 외부 라이브러리 (pip install anthropic tavily-python rich pydantic) ---
from anthropic import AsyncAnthropic
from tavily import TavilyClient
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.table import Table

# 환경 변수 로드
load_dotenv()

# API 키 설정
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not ANTHROPIC_API_KEY or not TAVILY_API_KEY:
    raise ValueError("❌ .env 파일에 API KEY를 설정해주세요!")

# 클라이언트 설정 (Anthropic은 비동기 클라이언트 사용)
# Tavily는 동기 클라이언트이므로 run_in_executor로 래핑하여 사용
aclient = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
console = Console()

# 모델 설정
FAST_MODEL = "claude-3-5-haiku-20241022"
SMART_MODEL = "claude-sonnet-4-5-20250929"  

# --- Pydantic 데이터 모델 (데이터 구조화) ---

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
        """모든 수집된 정보를 문자열로 반환"""
        text = "## Scout 정찰 정보\n"
        for item in self.scout_data:
            text += f"### Q: {item.query}\n{item.content}\n\n"
        
        if self.additional_data:
            text += "## Writer 추가 리서치 정보\n"
            for item in self.additional_data:
                text += f"### Q: {item.query}\n{item.content}\n\n"
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

    # ThreadPoolExecutor에서 실행하여 Non-blocking 구현
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
        console.print(Panel(f"[bold green]{self.name}[/bold green] 가 정찰을 시작합니다...", border_style="green"))
        
        queries = [
            (f"{ctx.destination} 입국 규정 비자 필수 요건", "advanced"),
            (f"{ctx.destination} 여행 치안 주의사항", "basic"),
        ]
        if ctx.keywords:
            queries.append((f"{ctx.destination} {ctx.keywords[0]} 추천 명소", "basic"))

        # Rich Progress Bar와 함께 병렬 실행
        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]정보 수집 중...", total=len(queries))
            
            # asyncio.gather로 병렬 처리
            tasks = [async_tavily_search(q, d) for q, d in queries]
            
            for completed_task in asyncio.as_completed(tasks):
                result = await completed_task
                results.append(result)
                progress.advance(task)

        ctx.scout_data = results
        console.print(f"✅ [bold green]정찰 완료:[/bold green] {len(results)}개 주제에 대한 정보 수집됨")
        return ctx


class ArchitectAgent:
    """🏗️ Architect Agent: 동적 템플릿 설계"""

    def __init__(self):
        self.name = "Architect Agent"

    async def run(self, ctx: TripContext) -> TripContext:
        console.print(Panel(f"[bold blue]{self.name}[/bold blue] 가 템플릿을 설계합니다...", border_style="blue"))

        scout_summary = ctx.get_combined_info()
        
        prompt = f"""
당신은 여행 보고서 설계자입니다.
수집된 정보를 바탕으로 '{ctx.destination}' 여행을 위한 최적의 목차(Template)를 작성하세요.

[수집된 정보]
{scout_summary}

[사용자 키워드]
{', '.join(ctx.keywords)}

[지침]
1. 일반적인 여행 정보(항공, 숙박, 교통) 외에 수집된 정보의 '특이사항(경고, 필수요건)'을 상단에 배치하세요.
2. 사용자 키워드 관련 섹션을 구체적으로 만드세요.
3. 번호가 매겨진 목차 형식으로만 출력하세요. 설명은 필요 없습니다.
"""
        response = await aclient.messages.create(
            model=FAST_MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        ctx.template = response.content[0].text
        console.print(Markdown(f"**생성된 템플릿 요약:**\n{ctx.template[:200]}..."))
        return ctx


class WriterAgent:
    """✍️ Writer Agent: Gap Analysis(지능형 부족 정보 분석) + 리포트 작성"""

    def __init__(self):
        self.name = "Writer Agent"

    async def run(self, ctx: TripContext) -> str:
        console.print(Panel(f"[bold magenta]{self.name}[/bold magenta] 가 보고서를 작성합니다...", border_style="magenta"))

        # 1. Gap Analysis (지능형 부족 정보 파악)
        console.print("[dim]🧠 현재 정보와 템플릿을 비교하여 부족한 정보를 분석 중...[/dim]")
        gap_queries = await self._analyze_gaps(ctx)
        
        # 2. 추가 리서치 (필요한 경우에만)
        if gap_queries:
            console.print(f"[bold yellow]🔍 추가 리서치 필요:[/bold yellow] {len(gap_queries)}건")
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                progress.add_task("[yellow]추가 정보 검색 중...", total=None)
                # 병렬 검색
                tasks = [async_tavily_search(q) for q in gap_queries]
                additional_results = await asyncio.gather(*tasks)
                ctx.additional_data = additional_results
        else:
            console.print("[bold green]✨ 추가 검색 불필요 (정보 충분)[/bold green]")

        # 3. 최종 작성
        console.print("[dim]📝 최종 보고서 생성 중...[/dim]")
        final_report = await self._write_final_report(ctx)
        
        return final_report

    async def _analyze_gaps(self, ctx: TripContext) -> List[str]:
        """LLM을 통해 템플릿 작성에 부족한 정보가 무엇인지 판단하고 검색 쿼리 생성"""
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
            # JSON 파싱 시도 (LLM이 마크다운 코드블럭을 쓸 경우 처리)
            cleaned_json = content.replace("```json", "").replace("```", "").strip()
            queries = json.loads(cleaned_json)
            return queries if isinstance(queries, list) else []
        except:
            console.print("[red]⚠️ Gap Analysis 파싱 실패, 추가 검색 생략[/red]")
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
3. **분량 조절(중요):** 각 섹션은 핵심만 간결하게 작성하고, 리스트 항목은 **최대 5개**로 제한하세요. 너무 길어지면 출력이 잘릴 수 있습니다.
4. 정보가 없는 항목은 '정보를 찾을 수 없음'이라 적지 말고, 일반적인 팁으로 대체하세요.
5. **결론** 섹션에는 이 여행지의 매력을 한 줄로 요약하는 문구를 넣으세요.
6. 마지막에 면책 조항(정보의 시의성 등)을 작은 글씨로 추가하세요.
"""
        response = await aclient.messages.create(
            model=SMART_MODEL, # 고성능 모델 사용
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text


# --- 메인 오케스트레이터 ---

async def main():
    # 타이틀 출력
    console.print(Panel.fit(
        "[bold yellow]✈️ TripPrep v2.0 AI[/bold yellow]\n"
        "[dim]Powered by Claude 3.5 & Tavily & Asyncio[/dim]",
        border_style="yellow"
    ))

    # 사용자 입력
    destination = console.input("[bold green]📍 여행지 입력 (예: 오사카): [/bold green]").strip() or "오사카"
    keywords_input = console.input("[bold green]🔑 키워드 입력 (콤마 구분, 예: 맛집,쇼핑): [/bold green]").strip()
    keywords = [k.strip() for k in keywords_input.split(",")] if keywords_input else ["맛집", "쇼핑"]

    # 컨텍스트 초기화
    ctx = TripContext(destination=destination, keywords=keywords)

    # 에이전트 초기화
    scout = ScoutAgent()
    architect = ArchitectAgent()
    writer = WriterAgent()

    try:
        # 1. Scout 실행
        ctx = await scout.run(ctx)
        
        # 2. Architect 실행
        ctx = await architect.run(ctx)
        
        # 3. Writer 실행
        final_report = await writer.run(ctx)

        # 결과 저장 및 출력
        filename = f"TripPrep_{destination}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(final_report)

        console.print(Panel(
            Markdown(final_report[:500] + "\n\n...(생략)..."),
            title=f"📄 보고서 미리보기 ({filename})",
            border_style="cyan"
        ))
        
        console.print(f"\n[bold green]🎉 모든 작업이 완료되었습니다! {filename} 파일을 확인하세요.[/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]❌ 치명적 오류 발생: {str(e)}[/bold red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())