from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.impl.gpt_sherlock import GptSherlock
from app.impl.nmap_sherlock import NMapSherlock
from app.impl.sqlmap_sherlock import SqlMapSherlock
from openai import AsyncOpenAI
import os
from typing import Literal
import asyncio

router = APIRouter(prefix="/test")


class TestRequest(BaseModel):
    url: str


sherlocks = [
    GptSherlock(),
    NMapSherlock(),
    SqlMapSherlock(),
]

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@router.post("/")
async def test(request: TestRequest):
    for sherlock in sherlocks:
        await sherlock.ready()
    return {
        "url": request.url,
        "response": sum(
            [await sherlock.run(request.url) for sherlock in sherlocks], []
        ),
    }


class Vulnerability(BaseModel):
    """
    export interface Vulnerability {
        id: string;
        scan_id: string;
        vulnerability_type: string;
        severity: "critical" | "high" | "medium" | "low" | "info";
        title: string;
        description?: string;
        evidence?: string;
        affected_url?: string;
        method?: string;
        parameter?: string;
        payload?: string;
        recommendation?: string;
        cwe_id?: string;
        cvss_score?: number;
        status: "open" | "fixed" | "accepted" | "false_positive";
        created_at: string;
        type: string;
        url: string;
    }
    """

    id: str
    scan_id: str
    vulnerability_type: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    title: str
    description: str | None = None
    evidence: str | None = None
    affected_url: str | None = None
    method: str | None = None
    parameter: str | None = None
    payload: str | None = None
    recommendation: str | None = None
    cwe_id: str | None = None
    cvss_score: float | None = None
    status: Literal["open", "fixed", "accepted", "false_positive"]
    created_at: str
    type: str
    url: str


class AnalysisRequest(BaseModel):
    url: str
    evidence: str
    vulnerability: Vulnerability


@router.post("/analysis")
async def test(request: AnalysisRequest):
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 정보보안 전문가입니다."},
            {
                "role": "user",
                "content": f"""
                주어진 증거에 따른 분석 결과를 알려주세요.
                증거: {request.evidence}
                취약점: {request.vulnerability}
                """,
            },
        ],
        stream=True,
    )

    async def async_generator():
        async for chunk in response:
            await asyncio.sleep(0)
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content
            else:
                yield ""

    return StreamingResponse(async_generator(), media_type="text/event-stream")
