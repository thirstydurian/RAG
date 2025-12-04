from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from tripprep_system import TripPrepSystem
from notion_integration import send_report_to_notion, create_checklist_in_notion

router = APIRouter(prefix="/api/tripprep", tags=["tripprep"])

# 시스템 인스턴스 (앱 시작 시 초기화됨)
system = TripPrepSystem()

class TripRequest(BaseModel):
    destination: str
    keywords: List[str] = []

class TripResponse(BaseModel):
    report: str

class NotionReportRequest(BaseModel):
    report: str
    destination: str

class NotionChecklistRequest(BaseModel):
    report: str
    destination: str

@router.post("/generate", response_model=TripResponse)
async def generate_report(request: TripRequest):
    """
    여행 보고서 생성 엔드포인트
    """
    if not request.destination:
        raise HTTPException(status_code=400, detail="Destination is required")
    
    try:
        # 키워드가 없으면 기본값 설정
        keywords = request.keywords if request.keywords else ["관광", "맛집"]
        
        # 보고서 생성 (비동기 호출)
        report = await system.generate_report(request.destination, keywords)
        
        return TripResponse(report=report)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notion/send-report")
async def send_to_notion(request: NotionReportRequest):
    """
    생성된 보고서를 Notion 페이지에 전송
    """
    try:
        success = send_report_to_notion(request.report, request.destination)
        return {"success": success, "message": "보고서가 Notion에 전송되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notion/create-checklist")
async def create_checklist(request: NotionChecklistRequest):
    """
    보고서에서 체크리스트를 추출하여 Notion 데이터베이스에 생성
    """
    try:
        # 체크리스트 추출
        checklist_items = await system.checklist.extract_checklist(
            request.report, 
            request.destination
        )
        
        if not checklist_items:
            raise HTTPException(status_code=500, detail="체크리스트 추출 실패")
        
        # Notion에 생성 (destination 전달)
        success = create_checklist_in_notion(checklist_items, request.destination)
        
        return {
            "success": success, 
            "message": f"{len(checklist_items)}개의 체크리스트 항목이 Notion에 생성되었습니다.",
            "items_count": len(checklist_items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
