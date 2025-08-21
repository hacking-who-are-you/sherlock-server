import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import re
import smtplib
import requests

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/traffic")

ATTACK_PATTERNS = {
    "xss": [
        re.compile(r"""<script|onerror|onload|javascript:|<svg|alert""", re.IGNORECASE),
    ],
    "sqli": [
        re.compile(
            r"""(--|\#|/\*|' OR 1=1|UNION\s+SELECT|SLEEP\s*\(|BENCHMARK\s*\()""",
            re.IGNORECASE,
        ),
    ],
    "pathtraversal": [re.compile(r"""\.\.[/\\]|%2e%2e""")],
}


def check_for_threats(url: str, body: str) -> dict:
    """
    Checks the given URL and body against a set of attack patterns.

    Args:
        url: The request URL.
        body: The request body.

    Returns:
        A dictionary indicating which threat types were detected.
    """
    detected_threats = {"xss": 0, "sqli": 0, "pathtraversal": 0}

    text_to_check = url + " " + body

    for threat_type, patterns in ATTACK_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text_to_check):
                detected_threats[threat_type] = 1
                break

    return detected_threats


# 수집되는 HTTP 로그(평면 JSON) 모델.
class IncomingHttpLog(BaseModel):
    """
    수집되는 HTTP 로그(평면 JSON) 모델.

    예시:
    {
        "client_ip": "127.0.0.1",
        "method": "POST",
        "url": "http://localhost:8000/items",
        "headers": {"host": "localhost:8000", "user-agent": "curl/8.14.1", ...},
        "request_body": "{name: John, age: 30}",
        "status_code": 307,
        "process_time_ms": 0
    }

    비고:
    - timestamp는 클라이언트가 보내지 않아도 되며, 서버에서 수신 시각(received_at)을 추가 저장합니다.
    """

    client_ip: Optional[str] = Field(default=None)
    method: str
    url: str
    headers: Dict[str, Any] = Field(default_factory=dict)
    request_body: Optional[str] = Field(default=None)
    status_code: int
    process_time_ms: Optional[int] = Field(default=None)


@router.get("/logs")
async def get_logs(date: str = Query(..., description="Date in YYYY-MM-DD format")):
    log_dir = os.getenv("TRAFFIC_LOG_DIR") or "./traffic_logs"
    log_file_path = os.path.join(log_dir, f"{date}.jsonl")

    if not os.path.exists(log_file_path):
        return {"error": "Log file not found for the given date."}

    try:
        with open(log_file_path, "r", encoding="utf-8") as log_file:
            logs = [json.loads(line) for line in log_file]
        return {"logs": logs}
    except Exception as e:
        logging.error(f"Error reading log file: {e}")
        return {"error": "An error occurred while reading the log file."}


@router.post("/logs")
async def ingest_logs(
    payload: Union[IncomingHttpLog, List[IncomingHttpLog]] = Body(...),
) -> Dict[str, Any]:
    logs = payload if isinstance(payload, list) else [payload]
    ts = datetime.now(timezone.utc).isoformat()
    records = []
    for log in logs:
        d = log.model_dump() if hasattr(log, "model_dump") else log.dict()
        d["received_at"] = ts
        d["threats"] = check_for_threats(d["url"], d["request_body"])
        if sum(d["threats"].values()) > 0:
            email_sender = smtplib.SMTP(
                os.getenv("EMAIL_SERVER"), os.getenv("EMAIL_PORT")
            )
            email_sender.starttls()
            email_sender.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
            email_sender.sendmail(
                os.getenv("EMAIL_FROM"),
                os.getenv("EMAIL_TO"),
                f"Threat detected: {d['url']}\n"
                f"Threat type: {d['threats']}\n"
                f"Threat evidence: {d['request_body']}\n"
                f"Threat timestamp: {d['received_at']}\n"
                f"Threat IP: {d['client_ip']}\n"
                f"Threat method: {d['method']}\n"
                f"Threat status code: {d['status_code']}\n",
            )

        watson_response = requests.post(
            os.getenv("WATSON_API_URL"),
            data={
                "client_ip": d["client_ip"],
                "method": d["method"],
                "url": d["url"],
                "headers": d["headers"],
                "request_body": d["request_body"],
                "status_code": d["status_code"],
                "process_time_ms": d["process_time_ms"],
            },
        )
        watson_data = watson_response.json()
        d["watson"] = watson_data
        records.append(json.dumps(d, ensure_ascii=False, separators=(",", ":")) + "\n")

    log_dir = os.getenv("TRAFFIC_LOG_DIR") or "./traffic_logs"
    os.makedirs(log_dir, exist_ok=True)
    path = os.path.join(
        log_dir, f"{datetime.now(timezone.utc).date().isoformat()}.jsonl"
    )

    await asyncio.to_thread(
        lambda: open(path, "a", encoding="utf-8").writelines(records)
    )
    return {"accepted": len(records)}
