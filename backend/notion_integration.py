import os
from typing import List, Dict
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

# Notion API 설정
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_REPORT_PAGE_ID = os.getenv("NOTION_REPORT_PAGE_ID")
NOTION_CHECKLIST_DB_ID = os.getenv("NOTION_CHECKLIST_DB_ID")

# Notion 클라이언트 초기화
notion = Client(auth=NOTION_API_KEY) if NOTION_API_KEY else None


def send_report_to_notion(report_content: str, destination: str) -> bool:
    """
    여행 보고서를 Notion 페이지에 전송
    """
    if not notion or not NOTION_REPORT_PAGE_ID:
        raise ValueError("Notion API가 설정되지 않았습니다.")
    
    try:
        # 보고서를 마크다운 블록으로 변환
        blocks = []
        
        # 제목 추가
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": f"🌍 {destination} 여행 보고서"}}]
            }
        })
        
        # 보고서 내용을 줄 단위로 파싱하여 블록 생성
        lines = report_content.split('\n')
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_paragraph:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": ' '.join(current_paragraph)}}]
                        }
                    })
                    current_paragraph = []
                continue
            
            # 헤딩 처리
            if line.startswith('# '):
                if current_paragraph:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": ' '.join(current_paragraph)}}]
                        }
                    })
                    current_paragraph = []
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                    }
                })
            elif line.startswith('## '):
                if current_paragraph:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": ' '.join(current_paragraph)}}]
                        }
                    })
                    current_paragraph = []
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": line[3:]}}]
                    }
                })
            elif line.startswith('### '):
                if current_paragraph:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": ' '.join(current_paragraph)}}]
                        }
                    })
                    current_paragraph = []
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                    }
                })
            else:
                current_paragraph.append(line)
        
        # 마지막 단락 추가
        if current_paragraph:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": ' '.join(current_paragraph)}}]
                }
            })
        
        # Notion 페이지에 블록 추가
        notion.blocks.children.append(
            block_id=NOTION_REPORT_PAGE_ID,
            children=blocks
        )
        
        return True
        
    except Exception as e:
        print(f"Notion 전송 오류: {e}")
        raise


def create_checklist_in_notion(checklist_items: List[Dict]) -> bool:
    """
    체크리스트 항목을 Notion 데이터베이스에 생성
    
    checklist_items: [{"task": "...", "deadline": "...", "category": "..."}]
    """
    if not notion or not NOTION_CHECKLIST_DB_ID:
        raise ValueError("Notion API가 설정되지 않았습니다.")
    
    try:
        for item in checklist_items:
            # 데이터베이스에 페이지(항목) 생성
            notion.pages.create(
                parent={"database_id": NOTION_CHECKLIST_DB_ID},
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": item.get("task", "")
                                }
                            }
                        ]
                    },
                    "Deadline": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": item.get("deadline", "")
                                }
                            }
                        ]
                    },
                    "Category": {
                        "select": {
                            "name": item.get("category", "기타")
                        }
                    },
                    "Status": {
                        "select": {
                            "name": "Not started"
                        }
                    }
                }
            )
        
        return True
        
    except Exception as e:
        print(f"체크리스트 생성 오류: {e}")
        raise
