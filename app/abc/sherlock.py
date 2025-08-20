from openai import AsyncOpenAI
import os
from agents import Agent
from agents.mcp import MCPServerStdio
from pydantic import BaseModel
from typing import Literal, List

""" 
interface VulnerabilityResult {
  id: string;
  type: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  description?: string;
  url: string;
  evidence?: string;
  recommendation?: string;
  aiAnalysis?: string;
}
"""


class SherlockOutput(BaseModel):
    id: str
    type: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    description: str | None = None
    url: str
    evidence: str | None = None
    recommendation: str | None = None
    aiAnalysis: str | None = None


class Sherlock:
    def __init__(self):
        self.gpt = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.mcp_server = None
        self.agent = Agent(
            name="assistant",
            instructions="you are a cybersecurity expert",
            output_type=List[SherlockOutput],
        )

    async def ready(self):
        if self.mcp_server is not None and self.mcp_server.session is None:
            await self.mcp_server.connect()

    async def run(self, url: str) -> str:
        raise NotImplementedError()

    @staticmethod
    def find_mcp_server(name: str) -> MCPServerStdio:
        path = os.path.join(
            os.path.dirname(__file__),
            "../..",
            "mcp-for-security",
            f"{name}-mcp",
            "build",
            "index.js",
        )
        return MCPServerStdio(
            params={"command": "node", "args": [path, name]},
            client_session_timeout_seconds=1000,
        )
