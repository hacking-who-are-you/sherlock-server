from app.abc.sherlock import Sherlock
import nmap
import socket
import json
from urllib.parse import urlparse


class NMapSherlock(Sherlock):
    def __init__(self, url: str):
        super().__init__(url)

    async def run(self) -> str:
        hostname = urlparse(self.url).hostname
        ip = socket.gethostbyname(hostname)
        nm = nmap.PortScanner()
        result = nm.scan(ip, "22-443")

        open_ports = []
        if ip in result["scan"]:
            for port, service in result["scan"][ip]["tcp"].items():
                if service["state"] == "open":
                    open_ports.append(
                        {
                            "port": port,
                            "service": service["name"],
                        }
                    )

        response = await self.gpt.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 보안 전문가 입니다",
                },
                {
                    "role": "user",
                    "content": f"""
아래 nmap 스캔 결과를 분석해주세요:

{json.dumps(result)}

각 열린 포트/서비스에 대해서 다음 정보를 제공해주세요:
1. 잠재적인 취약점에 대한 설명
2. 영향을 받는 엔드포인트 (host, port, service)
3. 스캔 결과에서 나온 증거
4. 심각도 평가 (Critical, High, Medium, Low) 그리고 간단한 이유
5. 수정 방법
6. OWASP ASVS, WSTG, CAPEC, CWE 참조 (클릭 가능한 링크)

위험도를 기준으로 찾은 것을 우선 순위로 매기고, 현재 취약점이 공격당하고 있는지 여부를 강조해주세요.

다음 열린 포트와 서비스를 기반으로 합니다:
{json.dumps(open_ports)}

결과를 잘 포맷팅된 HTML 스니펫으로 반환해주세요. 각 섹션은 줄바꿈 (<br>)으로 구분해주세요.
마크다운 포맷 기호는 추가하지 마세요.
""",
                },
            ],
        )
        return response.choices[0].message.content
