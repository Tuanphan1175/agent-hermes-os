"""Wrapper cho Task Scheduler / cron local: nạp cấu hình Supabase + vault path
từ .streamlit/secrets.toml rồi chạy sync_obsidian.py.

Mục đích: tác vụ định kỳ chạy được mà KHÔNG cần set biến môi trường thủ công và
KHÔNG nhúng key vào định nghĩa task (key vẫn nằm trong secrets.toml gitignored).
Đọc qua secrets.toml (UTF-8) cũng tránh lỗi mã hoá khi path vault có tiếng Việt.

secrets.toml cần (ngoài các key Supabase sẵn có):
  OBSIDIAN_VAULT_PATH = "D:/BÁC SĨ CHÍNH MÌNH/Project/my-second-brain"

Dùng:
  python scripts/run_sync.py                 # đọc vault từ secrets.toml
  python scripts/run_sync.py "D:/other/vault" # ghi đè vault qua arg
"""
import os
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SECRETS = REPO / ".streamlit" / "secrets.toml"


def main() -> None:
    if not SECRETS.is_file():
        raise SystemExit(f"Không thấy secrets: {SECRETS}")
    with open(SECRETS, "rb") as f:
        secrets = tomllib.load(f)

    vault = (sys.argv[1] if len(sys.argv) > 1 else None) \
        or os.environ.get("OBSIDIAN_VAULT_PATH") \
        or secrets.get("OBSIDIAN_VAULT_PATH")
    if not vault:
        raise SystemExit("Thiếu vault path: thêm OBSIDIAN_VAULT_PATH vào secrets.toml hoặc truyền arg")

    rc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "sync_obsidian.py"), "--vault", vault]
    ).returncode
    sys.exit(rc)


if __name__ == "__main__":
    main()
