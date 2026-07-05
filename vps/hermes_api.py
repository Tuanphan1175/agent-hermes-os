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
import re
import subprocess

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import uuid

_POLICY_PATTERNS = (
    "unable to respond to this request",
    "appears to violate",
    "double press esc",
)

_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_NOISE = (
    "Query:", "Initializing agent", "Resume this session", "hermes --resume",
    "Session:", "Duration:", "Messages:", "────",
)


def clean_reply(raw: str) -> str:
    """Bóc câu trả lời thật khỏi output CLI (khung ╭─ Hermes ─╮ + dòng nhiễu)."""
    text = _ANSI.sub("", raw)
    lines = text.splitlines()

    # Ưu tiên: lấy nội dung giữa viền khung Hermes
    out, inside = [], False
    for ln in lines:
        s = ln.strip()
        if "╭" in s and "Hermes" in s:
            inside = True
            continue
        if s.startswith("╰"):
            inside = False
            continue
        if inside:
            out.append(s.strip("│").strip())
    cleaned = "\n".join(l for l in out if l).strip()
    if cleaned:
        return cleaned

    # Dự phòng: bỏ các dòng nhiễu đã biết
    keep = [l for l in lines if l.strip() and not l.strip().startswith(_NOISE)]
    return "\n".join(keep).strip()


def is_policy_error(text: str) -> bool:
    normalized = (text or "").lower()
    return any(pattern in normalized for pattern in _POLICY_PATTERNS)


API_KEY = os.environ["HERMES_API_KEY"]
HERMES_BIN = os.environ.get("HERMES_BIN", "hermes")
TIMEOUT = int(os.environ.get("HERMES_TIMEOUT", "120"))
# Ép model theo request: shim chèn cờ --model <model>. Đổi cờ qua env nếu CLI khác
# (mặc định --model theo NousResearch hermes-agent). Sanitize id -> chỉ là 1 argv.
MODEL_FLAG = os.environ.get("HERMES_MODEL_FLAG", "--model")
_MODEL_RE = re.compile(r"^[A-Za-z0-9/_.\-]{1,64}$")
TASKS_FILE = os.path.expanduser("~/.hermes/tasks.json")

# Đảm bảo thư mục lưu trữ tồn tại
os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)

app = FastAPI(title="Hermes API shim")

# Kích hoạt CORS hỗ trợ các truy cập cross-origin từ các domain phụ khác nhau
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    message: str
    model: str = None  # tùy chọn: ép model cho request này (Model Arena)


def _authorized(authorization: str) -> bool:
    # so sánh hằng-thời-gian, chống timing attack
    return hmac.compare_digest(authorization or "", f"Bearer {API_KEY}")


# Cơ chế lưu trữ JSON cho Kanban
def load_tasks() -> list:
    if not os.path.exists(TASKS_FILE):
        default_tasks = [
            {"id": "t_eeeebfaf", "title": "Launch the AIPB explainer – explainer video, landing page...", "description": "", "column": "todo", "priority": "medium", "assignee": "julian", "tags": [], "due_date": None, "position": 0},
            {"id": "t_d29e6580", "title": "Produce AIPB explainer video", "description": "", "column": "blocked", "priority": "medium", "assignee": "julian", "tags": [], "due_date": None, "position": 0},
            {"id": "t_f41ac2a1", "title": "Create a basic website", "description": "", "column": "blocked", "priority": "medium", "assignee": "julian", "tags": [], "due_date": None, "position": 1},
            {"id": "t_ac02e2d8", "title": "Build AIPB landing page", "description": "", "column": "done", "priority": "medium", "assignee": "julian", "tags": [], "due_date": None, "position": 0},
            {"id": "t_8aa8583a", "title": "Write AIPB Twitter thread", "description": "", "column": "done", "priority": "medium", "assignee": "julian", "tags": [], "due_date": None, "position": 1},
            {"id": "t_9c97bcaa", "title": "Record intro AIPB podcast episode", "description": "", "column": "done", "priority": "medium", "assignee": "julian", "tags": [], "due_date": None, "position": 2},
            {"id": "t_c36bf620", "title": "Outline AI SEO content and keywords for YouTube channels", "description": "", "column": "done", "priority": "medium", "assignee": "julian", "tags": [], "due_date": None, "position": 3}
        ]
        # Seeding 19 tasks
        for i in range(19):
            default_tasks.append({
                "id": f"t_done_{i}",
                "title": f"Optimize marketing copy for lead magnet funnel and campaign step {i+1}",
                "description": "",
                "column": "done",
                "priority": "medium",
                "assignee": "julian",
                "tags": [],
                "due_date": None,
                "position": 4 + i
            })
        save_tasks(default_tasks)
        return default_tasks
        
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_tasks(tasks: list):
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    column: str = "backlog"
    priority: str = "medium"
    assignee: str = None
    tags: list = []
    due_date: str = None


class TaskUpdate(BaseModel):
    title: str = None
    description: str = None
    column: str = None
    priority: str = None
    assignee: str = None
    tags: list = None
    due_date: str = None


class TaskMove(BaseModel):
    column: str
    moved_by: str = "user"


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

    # arg list (KHÔNG shell) -> mỗi phần là 1 argv, chống shell injection.
    cmd = [HERMES_BIN, "chat", "-q", msg]
    model = (body.model or "").strip()
    if model:
        if not _MODEL_RE.match(model):
            raise HTTPException(status_code=400, detail="invalid model id")
        # ép model: hermes chat --model <model> -q "<msg>"
        cmd = [HERMES_BIN, "chat", MODEL_FLAG, model, "-q", msg]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="hermes timeout")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"không tìm thấy lệnh {HERMES_BIN}")

    if proc.returncode != 0:
        err = proc.stderr or proc.stdout or "hermes error"
        if is_policy_error(err):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Upstream model refused this request. "
                    "Start a new session or rewrite the request as a narrow coding task. "
                    "Keep the request focused on repository files, commands, logs, "
                    "and software changes."
                ),
            )
        raise HTTPException(status_code=500, detail=err[-500:])

    return {"reply": clean_reply(proc.stdout)}


# --- KANBAN ENDPOINTS (Hỗ trợ React App workspace.tuandoctor.com/tasks) ---

@app.get("/api/hermes-tasks")
@app.get("/api/claude-tasks")
def get_tasks(column: str = None, assignee: str = None, priority: str = None, include_done: str = None):
    tasks = load_tasks()
    if column:
        tasks = [t for t in tasks if t.get("column") == column]
    if assignee:
        tasks = [t for t in tasks if t.get("assignee") == assignee]
    if priority:
        tasks = [t for t in tasks if t.get("priority") == priority]
    return {"tasks": tasks}


@app.get("/api/hermes-tasks-assignees")
@app.get("/api/claude-tasks-assignees")
def get_assignees():
    return {
        "assignees": [
            {"id": "julian", "label": "julian"}
        ],
        "humanReviewer": None
    }


@app.post("/api/hermes-tasks")
@app.post("/api/claude-tasks")
def create_task(body: TaskCreate):
    tasks = load_tasks()
    new_id = f"t_{uuid.uuid4().hex[:8]}"
    new_task = {
        "id": new_id,
        "title": body.title,
        "description": body.description,
        "column": body.column,
        "priority": body.priority,
        "assignee": body.assignee,
        "tags": body.tags,
        "due_date": body.due_date,
        "position": len(tasks)
    }
    tasks.insert(0, new_task)
    save_tasks(tasks)
    return {"task": new_task}


@app.patch("/api/hermes-tasks/{task_id}")
@app.patch("/api/claude-tasks/{task_id}")
def update_task(task_id: str, body: TaskUpdate):
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            if body.title is not None: t["title"] = body.title
            if body.description is not None: t["description"] = body.description
            if body.column is not None: t["column"] = body.column
            if body.priority is not None: t["priority"] = body.priority
            if body.assignee is not None: t["assignee"] = body.assignee
            if body.tags is not None: t["tags"] = body.tags
            if body.due_date is not None: t["due_date"] = body.due_date
            save_tasks(tasks)
            return {"task": t}
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/api/hermes-tasks/{task_id}")
@app.post("/api/claude-tasks/{task_id}")
def move_task(task_id: str, body: TaskMove, action: str = None):
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            t["column"] = body.column
            save_tasks(tasks)
            return {"task": t}
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/api/hermes-tasks/{task_id}")
@app.delete("/api/claude-tasks/{task_id}")
def delete_task(task_id: str):
    tasks = load_tasks()
    tasks = [t for t in tasks if t.get("id") != task_id]
    save_tasks(tasks)
    return {"status": "ok"}

