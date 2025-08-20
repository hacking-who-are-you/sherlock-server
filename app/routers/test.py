from fastapi import APIRouter
from pydantic import BaseModel
import requests

router = APIRouter(prefix="/test")


class TestRequest(BaseModel):
    url: str


@router.post("/")
async def test(request: TestRequest):
    res = requests.get(request.url)
    return {"url": request.url, "res": res.text}
