import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field
from collections import deque
from openai import AsyncOpenAI
from ..routers.trafficLog import get_logs  # 상단으로 이동

router = APIRouter(prefix="/traffic")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = logging.getLogger(__name__)

class AnalyzeRequest(BaseModel):
    date: str = Field(..., description="분석할 날짜 (YYYY-MM-DD)")
    limit: int = Field(default=500, ge=1, le=5000, description="분석할 로그 개수")
    hint: Optional[str] = Field(default=None, description="분석 포커스")

def _format_log_line(log: Dict[str, Any]) -> str:
    """로그를 읽기 쉬운 형태로 포맷팅"""
    ts = log.get("received_at", "")
    ip = log.get("client_ip", "-")
    method = log.get("method", "-")
    url = log.get("url", "-")
    status = log.get("status_code", "-")
    rt = log.get("process_time_ms", "-")
    return f"[{ts}] {ip} {method} {url} {status} rt={rt}ms"

@router.post("/analyze")
async def analyze_traffic(request: AnalyzeRequest) -> Dict[str, Any]:
    try:
        logger.info(f"Starting traffic analysis for date: {request.date}, limit: {request.limit}")
        
        # trafficLog의 GET 엔드포인트 호출
        log_response = await get_logs(request.date)
        
        if "error" in log_response:
            raise HTTPException(status_code=404, detail=log_response["error"])
        
        logs = log_response["logs"]
        logger.info(f"Retrieved {len(logs)} logs from trafficLog")
        
        # limit 적용
        if len(logs) > request.limit:
            logs = logs[-request.limit:]
            logger.info(f"Limited to last {request.limit} logs")
        
        # 로그 포맷팅
        formatted = [_format_log_line(log) for log in logs]
        
        # GPT 분석 
        system_prompt = (
            "당신은 세계 최고의 네트워크/웹 보안 분석가입니다. 아래 HTTP 요청/응답 로그 요약을 바탕으로 "
            "취약점 징후, 이상 트래픽 패턴(스캐닝, 브루트포싱, 크롤링), 인증/리다이렉션/오류 처리 문제, "
            "민감정보 노출 가능성 등을 분석하세요. 한국어로 간결하지만 구체적으로, 실행 가능한 조치를 포함해 작성하세요. "
            "구성: 1) 요약 2) 주요 발견(증거 포함) 3) 위험도/영향 4) 권고 5) 부록(로그 근거 샘플)."
        )

        user_content = (
            f"분석 대상 날짜: {request.date}\n"
            f"로그 개수: {len(formatted)}\n"
            + (f"분석 포커스: {request.hint}\n" if request.hint else "")
            + "[로그 요약]\n"
            + "\n".join(formatted)
        )

        logger.info("Sending request to OpenAI for analysis")
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )

        analysis = resp.choices[0].message.content
        logger.info("Analysis completed successfully")
        
        return {
            "date": request.date, 
            "used_logs": len(formatted), 
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error during traffic analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")