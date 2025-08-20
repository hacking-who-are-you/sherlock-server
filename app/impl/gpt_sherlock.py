from app.abc.sherlock import Sherlock
import requests


class GptSherlock(Sherlock):
    def __init__(self):
        super().__init__()

    async def run(self, url: str) -> str:
        res = requests.get(url)
        response = await self.gpt.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "아래에 넘겨주는 HTML을 보고 취약점이 있을만한 부분을 알려줘.",
                },
                {"role": "user", "content": res.text},
            ],
        )
        return response.choices[0].message.content
