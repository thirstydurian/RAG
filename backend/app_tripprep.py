from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from tripprep_system import TripPrepSystem

router = APIRouter(prefix="/api/tripprep", tags=["tripprep"])

# 시스템 인스턴스 (앱 시작 시 초기화됨)
system = TripPrepSystem()

class TripRequest(BaseModel):
    destination: str
    keywords: List[str] = []

class TripResponse(BaseModel):
    report: str

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
