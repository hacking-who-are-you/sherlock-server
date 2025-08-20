import os
from app.abc.sherlock import Sherlock
import requests
from openai import AsyncOpenAI
import nmap
import socket
import json
from urllib.parse import urlparse


class NMapSherlock(Sherlock):
    def __init__(self, url: str):
        super().__init__(url)
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def run(self) -> str:
        hostname = urlparse(self.url).hostname
        ip = socket.gethostbyname(hostname)
        nm = nmap.PortScanner()
        result = nm.scan(ip, "22-443")

        open_ports = []
        for port, service in result["scan"][ip]["tcp"].items():
            if service["state"] == "open":
                open_ports.append(
                    {
                        "port": port,
                        "service": service["name"],
                    }
                )

        response = await self.client.chat.completions.create(
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

For each open port/service, provide:
1. A description of potential vulnerabilities
2. The affected endpoint (host, port, service)
3. Evidence from the scan
4. Severity rating (Critical, High, Medium, Low) and a brief rationale
5. Remediation steps
6. References to OWASP ASVS, WSTG, CAPEC, CWE (as clickable links)

Prioritize findings by risk to the business, and highlight any issues that are currently being exploited in the wild (if known).

Based on the following open ports and services detected:
{json.dumps(open_ports)}

Return the results as a well-formatted HTML snippet with line breaks (<br>) separating each section.
""",
                },
            ],
        )
        return response.choices[0].message.content
