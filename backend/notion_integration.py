import os
import re
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


def parse_markdown_to_rich_text(text: str) -> List[Dict]:
    """
    마크다운 텍스트를 Notion rich_text 형식으로 변환
    **bold**, [link](url) 등을 처리
    """
    rich_text = []
    
    # **bold** 패턴 찾기
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    
    for part in parts:
        if not part:
            continue
            
        if part.startswith('**') and part.endswith('**'):
            # Bold 텍스트
            content = part[2:-2]
            rich_text.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"bold": True}
            })
        else:
            # 링크 패턴 찾기 [text](url)
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            link_parts = re.split(link_pattern, part)
            
            i = 0
            while i < len(link_parts):
                if i + 2 < len(link_parts) and link_parts[i+2]:
                    # 링크 앞의 일반 텍스트
                    if link_parts[i]:
                        rich_text.append({
                            "type": "text",
                            "text": {"content": link_parts[i]}
                        })
                    # 링크
                    rich_text.append({
                        "type": "text",
                        "text": {
                            "content": link_parts[i+1],
                            "link": {"url": link_parts[i+2]}
                        }
                    })
                    i += 3
                else:
                    # 일반 텍스트
                    if link_parts[i]:
                        rich_text.append({
                            "type": "text",
                            "text": {"content": link_parts[i]}
                        })
                    i += 1
    
    return rich_text if rich_text else [{"type": "text", "text": {"content": text}}]


def send_report_to_notion(report_content: str, destination: str) -> bool:
    """
    여행 보고서를 Notion 페이지에 전송
    """
    if not notion or not NOTION_REPORT_PAGE_ID:
        raise ValueError("Notion API가 설정되지 않았습니다.")
    
    try:
        blocks = []
        
        # 제목 추가
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": f"🌍 {destination} 여행 보고서"}}]
            }
        })
        
        # 보고서 내용을 줄 단위로 파싱
        lines = report_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 빈 줄 건너뛰기
            if not line:
                i += 1
                continue
            
            # 헤딩 처리
            if line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": parse_markdown_to_rich_text(line[4:])
                    }
                })
                i += 1
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": parse_markdown_to_rich_text(line[3:])
                    }
                })
                i += 1
            elif line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": parse_markdown_to_rich_text(line[2:])
                    }
                })
                i += 1
            # 리스트 항목 처리
            elif line.startswith('- ') or line.startswith('* '):
                # 연속된 리스트 항목 수집
                list_items = []
                while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                    item_text = lines[i].strip()[2:]  # '- ' 제거
                    list_items.append(item_text)
                    i += 1
                
                # 리스트 블록 생성
                for item in list_items:
                    blocks.append({
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": parse_markdown_to_rich_text(item)
                        }
                    })
            # 번호 리스트 처리
            elif re.match(r'^\d+\.\s', line):
                # 연속된 번호 리스트 수집
                numbered_items = []
                while i < len(lines) and re.match(r'^\d+\.\s', lines[i].strip()):
                    item_text = re.sub(r'^\d+\.\s', '', lines[i].strip())
                    numbered_items.append(item_text)
                    i += 1
                
                # 번호 리스트 블록 생성
                for item in numbered_items:
                    blocks.append({
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": parse_markdown_to_rich_text(item)
                        }
                    })
            # 일반 단락
            else:
                # 연속된 일반 텍스트 수집 (빈 줄이나 특수 형식 만날 때까지)
                paragraph_lines = []
                while i < len(lines):
                    current = lines[i].strip()
                    if not current:
                        break
                    if (current.startswith('#') or 
                        current.startswith('- ') or 
                        current.startswith('* ') or 
                        re.match(r'^\d+\.\s', current)):
                        break
                    paragraph_lines.append(current)
                    i += 1
                
                if paragraph_lines:
                    # 줄바꿈 유지하면서 단락 생성
                    paragraph_text = '\n'.join(paragraph_lines)
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": parse_markdown_to_rich_text(paragraph_text)
                        }
                    })
        
        # Notion 페이지에 블록 추가 (100개씩 나눠서 전송)
        for i in range(0, len(blocks), 100):
            chunk = blocks[i:i+100]
            notion.blocks.children.append(
                block_id=NOTION_REPORT_PAGE_ID,
                children=chunk
            )
        
        return True
        
    except Exception as e:
        print(f"Notion 전송 오류: {e}")
        import traceback
        traceback.print_exc()
        raise


def create_checklist_in_notion(checklist_items: List[Dict]) -> bool:
    """
    체크리스트 항목을 Notion 페이지에 To-Do 리스트로 생성
    
    checklist_items: [{"task": "...", "deadline": "...", "category": "..."}]
    """
    if not notion or not NOTION_CHECKLIST_DB_ID:
        raise ValueError("Notion API가 설정되지 않았습니다.")
    
    try:
        # NOTION_CHECKLIST_DB_ID를 페이지 ID로 사용
        blocks = []
        
        # 제목 추가
        blocks.append({
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "✅ 여행 준비 체크리스트"}}]
            }
        })
        
        # 카테고리별로 그룹화
        categories = {}
        for item in checklist_items:
            category = item.get("category", "기타")
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        # 카테고리별로 체크리스트 생성
        for category, items in categories.items():
            # 카테고리 헤딩
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": f"📌 {category}"}}]
                }
            })
            
            # 각 항목을 To-Do 블록으로 추가
            for item in items:
                task = item.get("task", "")
                deadline = item.get("deadline", "")
                
                # 체크박스 항목
                text_content = f"{task}"
                if deadline:
                    text_content += f" (⏰ {deadline})"
                
                blocks.append({
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": [{"type": "text", "text": {"content": text_content}}],
                        "checked": False
                    }
                })
        
        # Notion 페이지에 블록 추가
        notion.blocks.children.append(
            block_id=NOTION_CHECKLIST_DB_ID,  # 이제 페이지 ID로 사용
            children=blocks
        )
        
        return True
        
    except Exception as e:
        print(f"체크리스트 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        raise
