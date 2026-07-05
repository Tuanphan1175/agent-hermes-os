"""Export các bảng SQLite cục bộ ra backups/*.json để sao lưu.

Dùng:
  python scripts/backup_sqlite.py
"""
import json
import sys
from pathlib import Path

# Thêm thư mục gốc vào path để import local_db
REPO = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO))
import local_db

TABLES = ["obsidian_vault", "ai_spend", "mission_control", "ideas"]
out = REPO / "backups"
out.mkdir(exist_ok=True)

# 1) Backup các bảng thông thường
for table in TABLES:
    res = local_db.supabase.table(table).select("*").execute()
    data = res.data
    # Sắp xếp theo ID nếu có để đồng bộ lịch sử git diff
    if data and "id" in data[0]:
        try:
            data.sort(key=lambda x: x["id"])
        except Exception:
            pass
    
    path = out / f"{table}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{table}: {len(data)} hàng -> {path.name}")

# 2) Backup các bản ghi cụ thể từ datastore ra các file json riêng biệt
datastore_mappings = {
    "youtube-scripts": "youtube_scripts.json",
    "seo-campaigns": "seo_campaigns.json",
    "seo-transcripts": "seo_transcripts.json",
    "workspace-skills": "workspace_skills.json"
}

for key, filename in datastore_mappings.items():
    res = local_db.supabase.table("datastore").select("data").eq("key", key).execute()
    if res.data:
        # data trong SQLite được giải mã sẵn thành python object (list/dict) bởi wrapper
        content = res.data[0]["data"]
        path = out / filename
        path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"datastore[{key}] -> {path.name}")
