from fastapi import APIRouter
from pydantic import BaseModel
import requests
from openai import AsyncOpenAI
import os

router = APIRouter(prefix="/test")

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class TestRequest(BaseModel):
    url: str


@router.post("/")
async def test(request: TestRequest):
    res = requests.get(request.url)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "아래에 넘겨주는 HTML을 보고 취약점이 있을만한 부분을 알려줘.",
            },
            {"role": "user", "content": res.text},
        ],
    )
    return {
        "url": request.url,
        "res": res.text,
        "response": response.choices[0].message.content,
    }
