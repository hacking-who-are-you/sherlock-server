from app.abc.sherlock import Sherlock
import nmap
import socket
import json
from urllib.parse import urlparse
from agents import Runner


class NMapSherlock(Sherlock):
    def __init__(self):
        super().__init__()
        self.mcp_server = Sherlock.find_mcp_server("nmap")
        self.agent.mcp_servers.append(self.mcp_server)

    async def run(self, url: str) -> str:
        hostname = urlparse(url).hostname
        ip = socket.gethostbyname(hostname)
        result = await Runner.run(
            self.agent,
            f"""
            '{ip}'이 잠재적인 취약점이 있는 서비스라고 생각되면 취약점을 분석한 후에 결과를 알려주세요.
            다만 False Positive는 최대한 없도록 도구를 사용해서 취약점이 확인되지 않은 경우에는 취약점이 없는 것으로 판단해주세요.
            nmap을 사용해서 취약점을 찾기 때문에 포트 외에 다른 취약점은 찾이 말아주세요.

            각 열린 포트/서비스에 대해서 다음 정보를 제공해주세요:
            - description: 잠재적인 취약점에 대한 설명
            - type: 취약점 타입
            - severity: 심각도
            - url: 취약점이 있는 url
            - evidence: 증거
            - recommendation: 수정 방법
            - aiAnalysis: 추가적인 분석

            위험도를 기준으로 찾은 것을 우선 순위로 매기고, 현재 취약점이 공격당하고 있는지 여부를 강조해주세요.
            취약점이 발견되지 않은 경우에는 아무것도 출력하지 마세요.
            """,
        )
        print(result)
        return result.final_output
