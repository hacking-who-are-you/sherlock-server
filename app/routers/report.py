from fastapi import APIRouter
from pydantic import BaseModel
from openai import AsyncOpenAI
import os

router = APIRouter(prefix="/report")

class ReportRequest(BaseModel):
    type: str
    url: str
    analysis: str

@router.post("/")
async def generate_report(request: ReportRequest):
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system_prompt = (
        "당신은 세계 최고의 보안 컨설턴트입니다. 지금부터 외부 사이버 위협 분석 도구들로부터 분석한 결과가 당신에게 제공될 거에요." 
        "분석 대상은 네트워크 트래픽이거나, 특정 웹페이지에 대한 scan 결과입니다."
        "당신은 제공된 분석 결과를 바탕으로 고객사에 제출할 취약점 분석 리포트를 한국어로 작성해야 합니다. 반드시 다음 구조로, HTML로 작성해주세요:\n"
        "1) 요약\n2) 대상 타입(웹페이지 분석인지 트래픽 분석인지)\n3) 주요 발견 사항\n4) 위험도 및 영향\n5) 권고사항\n6) 부록(분석 근거)\n"
        "주요 발견 사항 및 위험도는 종합적인 중요도(발생 확률 및 영향도)를 기준으로 내림차순으로 정렬해서 중요한 것 우선으로 작성하세요."
        "각 항목은 간결하지만 구체적으로, 실행 가능한 조치 위주로 작성하고, 불확실한 내용은 가정임을 명시해주세요. 단계별로 생각하세요."
    )
    user_content = (
        f"대상 타입: {request.type}\n"
        f"대상 URL: {request.url}\n\n"
        f"[분석 결과(raw)]:\n{request.analysis}\n"
    )

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )

    report_text = response.choices[0].message.content
    return {
        "url": request.url,
        "report": report_text,
    }