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

            각 열린 포트/서비스에 대해서 다음 정보를 제공해주세요:
            1. 잠재적인 취약점에 대한 설명
            2. 영향을 받는 엔드포인트 (host, port, service)
            3. 스캔 결과에서 나온 증거
            4. 심각도 평가 (Critical, High, Medium, Low) 그리고 간단한 이유
            5. 수정 방법
            6. OWASP ASVS, WSTG, CAPEC, CWE 참조 (클릭 가능한 링크)

            위험도를 기준으로 찾은 것을 우선 순위로 매기고, 현재 취약점이 공격당하고 있는지 여부를 강조해주세요.
            """,
        )
        print(result)
        return result.final_output
