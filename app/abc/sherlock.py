from openai import AsyncOpenAI
import os


class Sherlock:
    def __init__(self, url: str):
        self.url = url
        self.gpt = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self) -> str:
        raise NotImplementedError()
