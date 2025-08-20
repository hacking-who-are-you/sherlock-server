from fastapi import APIRouter
from pydantic import BaseModel
from app.impl.gpt_sherlock import GptSherlock

router = APIRouter(prefix="/test")


class TestRequest(BaseModel):
    url: str


@router.post("/")
async def test(request: TestRequest):
    sherlocks = [GptSherlock(request.url)]
    return {
        "url": request.url,
        "response": [await sherlock.run() for sherlock in sherlocks],
    }
