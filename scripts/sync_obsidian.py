"""Đồng bộ vault Obsidian (local) -> bảng Supabase obsidian_vault.

Quét toàn bộ file .md trong vault, suy ra category theo folder, rồi ghi đè
toàn bộ bảng obsidian_vault (full re-sync: xóa sạch -> insert lại) để bảng
là bản phản chiếu trung thực của vault. Tabs Recent/Notes/Omi trên dashboard
sẽ hiển thị đúng ghi chú thật sau khi chạy.

Đọc cấu hình từ biến môi trường (KHÔNG hardcode key):
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY   (cần service_role để ghi, bỏ qua RLS)
  OBSIDIAN_VAULT_PATH         (hoặc truyền qua --vault)

Dùng:
  python scripts/sync_obsidian.py --vault "D:/Obsidian/MyVault" --dry-run
  python scripts/sync_obsidian.py --vault "D:/Obsidian/MyVault"
"""
import argparse
import os
import sys
import time
from pathlib import Path

from supabase import create_client

# Console Windows mặc định cp1252 không in được ký tự Unicode (path/tiếng Việt) -> ép UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Suy category từ tên folder (khớp quy ước Notes/Omi của dashboard).
# raw/ = transcript video/article -> Omi; còn lại -> Notes. Sửa nếu vault khác.
CATEGORY_RULES = {
    "raw": "Omi",
    "omi": "Omi",
}
DEFAULT_CATEGORY = "Notes"

# N note sửa-gần-nhất được gắn category "Recent" (override category folder),
# để tab Recent có nội dung dù vault không có folder "Memories".
RECENT_COUNT = 15

# Bỏ qua các folder hệ thống/không phải nội dung.
IGNORE_DIRS = {".obsidian", ".trash", ".git"}


def derive_category(rel_path: Path) -> str:
    parts = [p.lower() for p in rel_path.parts]
    for key, cat in CATEGORY_RULES.items():
        if key in parts:
            return cat
    return DEFAULT_CATEGORY


def humanize_age(mtime: float) -> str:
    """Đổi mtime thành chuỗi 'X ago' khớp giao diện (vd '45m ago', '2d ago')."""
    secs = max(0.0, time.time() - mtime)
    mins = secs / 60
    if mins < 60:
        return f"{int(mins)}m ago"
    hours = mins / 60
    if hours < 24:
        return f"{int(hours)}h ago"
    return f"{int(hours / 24)}d ago"


def scan_vault(vault: Path) -> list[dict]:
    """Trả về danh sách row đã sắp xếp mới-nhất-trước (để tab Recent đúng thứ tự)."""
    found: list[tuple[float, dict]] = []
    for md in vault.rglob("*.md"):
        rel = md.relative_to(vault)
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue
        mtime = md.stat().st_mtime
        found.append((mtime, {
            "file_name": md.stem,
            "file_path": rel.as_posix(),
            "category": derive_category(rel),
            "updated_at": humanize_age(mtime),
        }))
    found.sort(key=lambda t: t[0], reverse=True)
    rows = [row for _, row in found]
    # 15 note mới nhất -> Recent (override category folder).
    for row in rows[:RECENT_COUNT]:
        row["category"] = "Recent"
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Sync Obsidian vault -> Supabase obsidian_vault")
    ap.add_argument("--vault", default=os.environ.get("OBSIDIAN_VAULT_PATH"),
                    help="Đường dẫn folder vault Obsidian (hoặc đặt env OBSIDIAN_VAULT_PATH)")
    ap.add_argument("--dry-run", action="store_true", help="Chỉ xem trước, không ghi DB")
    args = ap.parse_args()

    if not args.vault:
        raise SystemExit("Thiếu vault path: dùng --vault hoặc đặt OBSIDIAN_VAULT_PATH")
    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        raise SystemExit(f"Vault không tồn tại hoặc không phải folder: {vault}")

    rows = scan_vault(vault)
    by_cat: dict[str, int] = {}
    for r in rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    print(f"Quét {vault}: {len(rows)} ghi chú .md  {by_cat}")

    if args.dry_run:
        for r in rows[:12]:
            print(f"  [{r['category']:>6}] {r['file_path']}  ({r['updated_at']})")
        print("(dry-run — KHÔNG ghi DB)")
        return

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise SystemExit("Thiếu SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY trong env")

    sb = create_client(url, key)
    # Full re-sync: xóa sạch (cần filter cho PostgREST) rồi insert lại.
    sb.table("obsidian_vault").delete().neq("id", 0).execute()
    if rows:
        sb.table("obsidian_vault").insert(rows).execute()
    print(f"Đã đồng bộ {len(rows)} ghi chú vào obsidian_vault.")


if __name__ == "__main__":
    main()
