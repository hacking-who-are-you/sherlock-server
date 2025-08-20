from app.abc.sherlock import Sherlock
import requests
from agents import Runner


class GptSherlock(Sherlock):
    def __init__(self):
        super().__init__()

    async def run(self, url: str) -> str:
        res = requests.get(url)
        result = await Runner.run(
            self.agent,
            f"""
        제시된 HTML 코드를 보고 전반적인 취약점을 찾아주세요.
        취약점 중 Sql Injection은 제외해주세요.
                                  
        HTML:
        {res.text}
        """,
        )
        return result.final_output
