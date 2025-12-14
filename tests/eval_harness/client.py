import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class ChatResponse:
    text: str
    raw: Dict[str, Any]
    latency_ms: int
    conversation_id: Optional[str] = None

class ChatClient:
    """
    Real API client for POST /api/user/chat
    - Uses JSON body: {message, force_local, conversation_id, model, stream}
    - stream=False only (eval harness should be deterministic)
    - Auth:
        - DEBUG mode can bypass session cookie
        - PROD requires Cookie: session_token=...
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.endpoint = f"{self.base_url}/api/v1/user/chat"

        # Optional auth cookie for prod
        self.session_token = os.getenv("EVAL_SESSION_TOKEN")

        # Timeouts - keep conservative
        self.timeout = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)

    def _cookie_header(self) -> Dict[str, str]:
        if not self.session_token:
            return {}
        return {"Cookie": f"session_token={self.session_token}"}

    async def chat(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        force_local: bool = False,
    ) -> ChatResponse:
        payload = {
            "message": message,
            "force_local": force_local,
            "conversation_id": conversation_id,
            "model": model,
            "stream": False,  # Eval harness: non-stream only
        }

        headers = {"Content-Type": "application/json", **self._cookie_header()}

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(self.endpoint, headers=headers, json=payload)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        # Auth failures should be explicit
        if resp.status_code == 401:
            raise RuntimeError(
                "401 Unauthorized. Prod ortaminda EVAL_SESSION_TOKEN env ile session_token cookie vermelisiniz."
            )

        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # 500 dönen response body bazen FastAPI error detail içerir
            print("STATUS:", resp.status_code)
            print("RESPONSE TEXT:", resp.text[:5000])  # çok uzunsa kes
            raise
        data = resp.json()
        text = (
            data.get("reply")
            or data.get("answer")
            or data.get("text")
            or data.get("content")
            or json.dumps(data, ensure_ascii=False)
        )

        conv_id = data.get("conversation_id")

        return ChatResponse(text=text, raw=data, latency_ms=elapsed_ms, conversation_id=conv_id)

