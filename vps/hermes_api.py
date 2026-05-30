"""HTTP shim bọc `hermes chat -q` để dashboard gọi Hermes agent thật.

Chạy trên VPS (cùng máy có lệnh `hermes`). KHÔNG hardcode key — đọc từ env:
  HERMES_API_KEY   token Bearer client phải gửi (bắt buộc)
  HERMES_BIN       đường dẫn lệnh hermes (mặc định: "hermes")
  HERMES_TIMEOUT   giây tối đa cho 1 lượt (mặc định: 120)

Chạy:
  pip install -r requirements.txt
  HERMES_API_KEY=... uvicorn hermes_api:app --host 127.0.0.1 --port 9100
"""
import hmac
import os
import subprocess

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

API_KEY = os.environ["HERMES_API_KEY"]
HERMES_BIN = os.environ.get("HERMES_BIN", "hermes")
TIMEOUT = int(os.environ.get("HERMES_TIMEOUT", "120"))

app = FastAPI(title="Hermes API shim")


class ChatIn(BaseModel):
    message: str


def _authorized(authorization: str) -> bool:
    # so sánh hằng-thời-gian, chống timing attack
    return hmac.compare_digest(authorization or "", f"Bearer {API_KEY}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(body: ChatIn, authorization: str = Header(default="")):
    if not _authorized(authorization):
        raise HTTPException(status_code=401, detail="unauthorized")

    msg = body.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="empty message")

    try:
        # arg list (KHÔNG shell) -> msg là 1 argv, chống shell injection
        proc = subprocess.run(
            [HERMES_BIN, "chat", "-q", msg],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="hermes timeout")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"không tìm thấy lệnh {HERMES_BIN}")

    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=(proc.stderr or "hermes error")[-500:])

    return {"reply": proc.stdout.strip()}
