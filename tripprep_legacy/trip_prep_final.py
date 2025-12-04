# trip_prep_final.py
"""
TripPrep 최종 버전 - Tavily 검색 통합
- Agent 1 (Scout): 넓고 얕은 정찰 검색
- Agent 2 (Architect): 동적 템플릿 커스터마이징
- Agent 3 (Writer): 부족한 정보 재검색 + 보고서 작성
"""

from dotenv import load_dotenv
import os
import anthropic
from tavily import TavilyClient
from typing import List, Dict

# .env 파일 로드
load_dotenv()

# API 키 확인
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not ANTHROPIC_API_KEY or not TAVILY_API_KEY:
    raise ValueError("❌ .env 파일에 ANTHROPIC_API_KEY와 TAVILY_API_KEY를 설정하세요!")

# 클라이언트 초기화
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# 모델 설정
SCOUT_MODEL = "claude-3-5-haiku-20241022"      # Agent 1, 2: 빠르고 저렴
WRITER_MODEL = "claude-sonnet-4-5-20250929"    # Agent 3: 최고 품질 (Sonnet 4.5 최신!)


class ScoutAgent:
    """
    Agent 1: 정찰병 (Scout)
    - 역할: 여행지의 주의사항, 특이사항, 법적 요구사항을 넓고 얕게 검색
    - 목표: "무엇이 중요한가?" 파악
    """
    
    def __init__(self):
        self.name = "🕵️ Scout Agent"
    
    def scout(self, destination: str, keywords: List[str]) -> Dict[str, str]:
        """
        정찰 검색 수행
        """
        print(f"\n{'='*60}")
        print(f"{self.name}: 정찰 시작")
        print(f"{'='*60}")
        print(f"📍 대상: {destination}")
        print(f"🔑 키워드: {keywords}")
        
        # 1. 법적 요구사항 검색 (신뢰도 최우선)
        print(f"\n[1/3] 법적 요구사항 검색 중...")
        legal_query = f"{destination} 입국 규정 비자 외교부 필수 요건"
        legal_results = self._search_with_tavily(
            legal_query,
            search_depth="advanced",
            include_domains=["mofa.go.kr", "0404.go.kr"]
        )
        
        # 2. 주의사항 및 특이사항 검색
        print(f"\n[2/3] 주의사항 검색 중...")
        warning_query = f"{destination} 여행 주의사항 금지 사항 특이사항"
        warning_results = self._search_with_tavily(
            warning_query,
            search_depth="basic"
        )
        
        # 3. 키워드 관련 검색 (첫 번째 키워드만)
        keyword_results = ""
        if keywords:
            print(f"\n[3/3] 키워드({keywords[0]}) 검색 중...")
            keyword_query = f"{destination} {keywords[0]} 추천"
            keyword_results = self._search_with_tavily(
                keyword_query,
                search_depth="basic"
            )
        
        print(f"\n✅ {self.name}: 정찰 완료!")
        
        return {
            'legal_info': legal_results,
            'warning_info': warning_results,
            'keyword_info': keyword_results
        }
    
    def _search_with_tavily(self, query: str, search_depth: str = "basic", 
                           include_domains: List[str] = None) -> str:
        """
        Tavily로 검색하고 결과를 문자열로 반환
        """
        try:
            results = tavily_client.search(
                query=query,
                search_depth=search_depth,
                max_results=3,
                include_domains=include_domains
            )
            
            # 검색 결과를 텍스트로 변환
            output = f"## {query}\n\n"
            
            if 'results' in results:
                for i, result in enumerate(results['results'], 1):
                    output += f"### 출처 {i}: {result.get('title', 'N/A')}\n"
                    output += f"URL: {result.get('url', 'N/A')}\n"
                    output += f"{result.get('content', 'N/A')}\n\n"
                    
                print(f"   ✓ {len(results['results'])}개 결과 발견")
            else:
                output += "검색 결과 없음\n\n"
                print(f"   ⚠️ 검색 결과 없음")
            
            return output
            
        except Exception as e:
            print(f"   ❌ 검색 실패: {str(e)}")
            return f"## {query}\n\n검색 실패: {str(e)}\n\n"


class ArchitectAgent:
    """
    Agent 2: 설계자 (Architect)
    - 역할: Scout의 정찰 결과를 분석하여 템플릿 커스터마이징
    - 목표: 여행지에 맞는 "맞춤형 목차" 생성
    """
    
    def __init__(self):
        self.name = "🏗️ Architect Agent"
        self.base_template = """
<보고서 템플릿>
1. 해당 국가 특이사항
2. 필수 법적 요구사항
   a. 비자/무비자 규정
   b. 여권 유효기간
   c. 거주지 등록 의무
3. 항공
   a. 플랫폼 추천
   b. 저렴한 시기
4. 숙박
   a. 추천 지역
5. 통신
   a. USIM
   b. eSIM
6. 현지 결제 & 환전
7. 현지 교통수단
8. 필수 앱
9. 준비물
10. 주요 관광지
    a. 미리 알고 가면 좋을 정보
    b. 역사적 의의 
    c. 현지 가이드가 설명할 법한 내용
    d. 사진 찍기 좋은 스팟
11. 기념품, 특산물
12. 사용자 키워드 관련 내용
</보고서 템플릿>
"""
    
    def design_template(self, scout_results: Dict[str, str], 
                       destination: str, keywords: List[str]) -> str:
        """
        Scout 결과를 바탕으로 템플릿 커스터마이징
        """
        print(f"\n{'='*60}")
        print(f"{self.name}: 템플릿 설계 시작")
        print(f"{'='*60}")
        
        prompt = f"""
당신은 여행 보고서 템플릿을 설계하는 전문가입니다.

<기본_템플릿>
{self.base_template}
</기본_템플릿>

<여행지>
{destination}
</여행지>

<사용자_키워드>
{', '.join(keywords)}
</사용자_키워드>

<Scout_정찰_결과>
{scout_results['legal_info']}

{scout_results['warning_info']}
</Scout_정찰_결과>

작업:
1. Scout의 정찰 결과를 분석하여 중요한 이슈를 찾으세요.
   - "필수", "의무", "등록", "금지", "제한", "주의", "경고", "벌금" 등의 키워드에 주목
   
2. 중요한 특수사항이 있으면 템플릿에 새로운 섹션을 추가하세요:
   - "1. 해당 국가 특이사항" 바로 뒤에 추가
   - 예: "1-1. ⚠️ 필수 거주지 등록 절차"
   
3. 사용자 키워드({', '.join(keywords)})를 "12. 사용자 키워드 관련 내용"에 구체화:
   - 12-a. {keywords[0] if keywords else '관광'} 관련 정보
   - 12-b. {keywords[1] if len(keywords) > 1 else '기타'} 관련 정보

4. 커스터마이징된 템플릿만 출력하세요 (설명 없이).

출력 형식:
<보고서 템플릿>
1. 해당 국가 특이사항
[필요시 추가 섹션]
2. 필수 법적 요구사항
...
</보고서 템플릿>
"""

        try:
            message = anthropic_client.messages.create(
                model=SCOUT_MODEL,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            customized_template = message.content[0].text
            
            print(f"✅ {self.name}: 템플릿 설계 완료!")
            print(f"\n📋 커스터마이징된 템플릿:")
            print(customized_template)
            
            return customized_template
            
        except Exception as e:
            print(f"❌ {self.name} 실패: {str(e)}")
            print(f"기본 템플릿 사용")
            return self.base_template


class WriterAgent:
    """
    Agent 3: 작가 (Writer & Researcher)
    - 역할: 템플릿의 각 항목을 채우고, 부족한 정보는 재검색
    - 목표: 완성된 보고서 작성
    """
    
    def __init__(self):
        self.name = "✍️ Writer Agent"
    
    def write_report(self, template: str, scout_results: Dict[str, str],
                    destination: str, keywords: List[str]) -> str:
        """
        보고서 작성 (필요시 재검색 포함)
        """
        print(f"\n{'='*60}")
        print(f"{self.name}: 보고서 작성 시작")
        print(f"{'='*60}")
        
        # Step 1: 템플릿 분석 및 부족한 정보 파악
        print(f"\n[1/2] 템플릿 분석 중...")
        missing_info = self._analyze_template(template, scout_results)
        
        # Step 2: 부족한 정보 재검색
        additional_info = ""
        if missing_info:
            print(f"\n[2/2] 부족한 정보 재검색 중...")
            additional_info = self._research_missing_info(destination, missing_info)
        else:
            print(f"\n[2/2] 재검색 불필요 (정보 충분)")
        
        # Step 3: 최종 보고서 작성
        print(f"\n📝 최종 보고서 작성 중...")
        report = self._generate_report(
            template, scout_results, additional_info, destination, keywords
        )
        
        print(f"\n✅ {self.name}: 보고서 작성 완료!")
        
        return report
    
    def _analyze_template(self, template: str, scout_results: Dict[str, str]) -> List[str]:
        """
        템플릿을 분석하여 부족한 정보 파악
        """
        # 실제로는 LLM으로 분석할 수 있지만, 간단하게 키워드 기반으로
        missing = []
        
        # 기본적으로 항공, 숙박, 교통 정보는 재검색
        if "항공" in template:
            missing.append("항공권 예약 팁")
        if "숙박" in template:
            missing.append("숙박 추천 지역")
        
        print(f"   부족한 정보: {len(missing)}개 항목")
        return missing
    
    def _research_missing_info(self, destination: str, 
                               missing_items: List[str]) -> str:
        """
        부족한 정보 재검색
        """
        additional = ""
        
        for item in missing_items[:2]:  # 최대 2개만 재검색 (비용 절감)
            print(f"   🔍 재검색: {item}")
            query = f"{destination} {item}"
            
            try:
                results = tavily_client.search(
                    query=query,
                    search_depth="basic",
                    max_results=2
                )
                
                if 'results' in results:
                    additional += f"\n### {item}\n"
                    for result in results['results']:
                        additional += f"{result.get('content', '')}\n"
                    print(f"      ✓ 정보 수집 완료")
                    
            except Exception as e:
                print(f"      ❌ 재검색 실패: {str(e)}")
        
        return additional
    
    def _generate_report(self, template: str, scout_results: Dict[str, str],
                        additional_info: str, destination: str, 
                        keywords: List[str]) -> str:
        """
        최종 보고서 생성
        """
        prompt = f"""
당신은 전문 여행 작가입니다. 초보 여행자를 위한 친절하고 실용적인 보고서를 작성하세요.

<여행지>
{destination}
</여행지>

<키워드>
{', '.join(keywords)}
</키워드>

<작성할_템플릿>
{template}
</작성할_템플릿>

<법적_정보_Scout_검색>
{scout_results['legal_info']}
</법적_정보_Scout_검색>

<주의사항_Scout_검색>
{scout_results['warning_info']}
</주의사항_Scout_검색>

<키워드_정보_Scout_검색>
{scout_results['keyword_info']}
</키워드_정보_Scout_검색>

<추가_정보_Writer_재검색>
{additional_info}
</추가_정보_Writer_재검색>

작업:
1. 템플릿의 각 항목을 위의 검색 정보를 바탕으로 작성하세요.
2. 법적 요구사항은 Scout의 검색 결과(외교부 등 공식 소스)를 최우선으로 사용하세요.
3. 중요한 주의사항은 ⚠️로 강조하세요.
4. 각 섹션을 2-3문장으로 간결하게 작성하세요.
5. 마크다운 형식으로 작성하세요 (제목은 ##, ### 사용).
6. 보고서 제목은 "# {destination} 여행 준비 보고서"로 시작하세요.

마지막에 다음 면책 조항을 추가하세요:

---
⚠️ **면책 조항**
- 이 보고서는 2025년 11월 기준으로 작성되었습니다.
- 법적 요구사항은 웹 검색 기반이나, 여행 전 반드시 외교부(0404.go.kr) 및 해당 국가 대사관에서 최신 정보를 확인하세요.
- 가격, 환율 등 변동 가능한 정보는 예약 시점에 재확인이 필요합니다.
"""

        try:
            message = anthropic_client.messages.create(
                model=WRITER_MODEL,  # Sonnet 사용 (고품질)
                max_tokens=5000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text
            
        except Exception as e:
            return f"# 오류\n\n보고서 작성 실패: {str(e)}"


class TripPrepSystem:
    """
    TripPrep 통합 시스템
    """
    
    def __init__(self):
        self.scout = ScoutAgent()
        self.architect = ArchitectAgent()
        self.writer = WriterAgent()
    
    def generate_report(self, destination: str, keywords: List[str]) -> str:
        """
        전체 파이프라인 실행
        """
        print("\n" + "="*70)
        print("🚀 TripPrep 보고서 생성 시작")
        print("="*70)
        print(f"📍 여행지: {destination}")
        print(f"🔑 키워드: {keywords}")
        print(f"🤖 모델: Scout/Architect={SCOUT_MODEL.split('-')[2]}, Writer={WRITER_MODEL.split('-')[2]}")
        
        # Agent 1: 정찰
        scout_results = self.scout.scout(destination, keywords)
        
        # input("\n▶️  Enter를 눌러 Agent 2 시작...")
        
        # Agent 2: 템플릿 설계
        customized_template = self.architect.design_template(
            scout_results, destination, keywords
        )
        
        # input("\n▶️  Enter를 눌러 Agent 2 시작...")
        
        # Agent 3: 보고서 작성
        report = self.writer.write_report(
            customized_template, scout_results, destination, keywords
        )
        
        print("\n" + "="*70)
        print("✨ TripPrep 보고서 생성 완료!")
        print("="*70)
        
        return report


def main():
    """
    메인 실행 함수
    """
    print("""
╔════════════════════════════════════════════════════════════╗
║          TripPrep 최종 버전 (Tavily 통합)                 ║
╚════════════════════════════════════════════════════════════╝

✨ 주요 기능:
  - Agent 1 (Scout): Tavily로 정찰 검색
  - Agent 2 (Architect): 동적 템플릿 설계
  - Agent 3 (Writer): 부족한 정보 재검색 + 보고서 작성
  
🔧 기술 스택:
  - 검색: Tavily API (AI 최적화)
  - LLM: Claude Haiku (Agent 1,2), Sonnet (Agent 3)
  - 비용: 효율적!
    """)
    
    # 사용자 입력
    destination = input("📍 여행지를 입력하세요 (예: 일본 도쿄): ").strip()
    if not destination:
        destination = "일본 도쿄"
        print(f"   → 기본값 사용: {destination}")
    
    keywords_input = input("🔑 관심 키워드를 입력하세요 (쉼표로 구분, 예: 온천,라멘): ").strip()
    if keywords_input:
        keywords = [k.strip() for k in keywords_input.split(",")]
    else:
        keywords = ["온천", "라멘"]
        print(f"   → 기본값 사용: {keywords}")
    
    # 시스템 초기화 및 실행
    system = TripPrepSystem()
    report = system.generate_report(destination, keywords)
    
    # 보고서 저장
    filename = f"report_{destination.replace(' ', '_')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📄 보고서가 저장되었습니다: {filename}")
    print(f"\n📋 보고서 미리보기:")
    print("="*70)
    print(report[:500] + "...\n")


if __name__ == "__main__":
    main()