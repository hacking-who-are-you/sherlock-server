from fastapi import APIRouter
from pydantic import BaseModel
from app.impl.gpt_sherlock import GptSherlock
from app.impl.nmap_sherlock import NMapSherlock
from app.impl.sqlmap_sherlock import SqlMapSherlock

router = APIRouter(prefix="/test")


class TestRequest(BaseModel):
    url: str


sherlocks = [
    GptSherlock(),
    NMapSherlock(),
    SqlMapSherlock(),
]


@router.post("/")
async def test(request: TestRequest):
    for sherlock in sherlocks:
        await sherlock.ready()
    return {
        "url": request.url,
        "response": [await sherlock.run(request.url) for sherlock in sherlocks],
    }
