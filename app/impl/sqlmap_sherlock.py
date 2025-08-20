from app.abc.sherlock import Sherlock
import nmap
import socket
import json
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
from agents import Runner


class SqlMapSherlock(Sherlock):
    def __init__(self):
        super().__init__()
        self.mcp_server = Sherlock.find_mcp_server("sqlmap")
        self.agent.mcp_servers.append(self.mcp_server)

    async def run(self, url: str) -> str:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        actions = [str(form) for form in soup.find_all("form")]
        print(actions)
        result = await Runner.run(
            self.agent,
            f"""
            '{url}'이 잠재적인 취약점이 있는 서비스라고 생각되면 취약점을 분석한 후에 결과를 알려주세요.
            다만 False Positive는 최대한 없도록 도구를 사용해서 취약점이 확인되지 않은 경우에는 취약점이 없는 것으로 판단해주세요.
            SqlMap을 사용해서 취약점을 찾기 때문에 form의 field 값들을 query string으로 변환한 url을 사용해야 합니다.
            Sql Injection 취약점외에 다른 취약점은 찾지 말아주세요.

            아래는 주어진 서비스의 소스코드에 있는 form들 입니다:
            {actions}

            취약점에 대해 다음 결과를 알려주세요:
            - description: 잠재적인 취약점에 대한 설명, form 태그 이름 또는 id
            - type: 취약점 타입
            - severity: 심각도
            - url: 취약점이 있는 url
            - evidence: 증거
            - recommendation: 수정 방법
            - aiAnalysis: 추가적인 분석

            취약점이 발견되지 않은 경우에는 아무것도 출력하지 마세요.
            """,
        )
        print(result)
        return result.final_output
