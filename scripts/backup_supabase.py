"""Export các bảng Supabase ra backups/*.json để Git Robot sao lưu hằng ngày.

Đọc cấu hình từ biến môi trường (GitHub Actions secrets), KHÔNG hardcode key:
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY   (server-side, bỏ qua RLS để đọc cả ai_spend)
"""
import json
import os
import pathlib

from supabase import create_client

URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TABLES = ["obsidian_vault", "ai_spend", "mission_control"]

sb = create_client(URL, KEY)
out = pathlib.Path("backups")
out.mkdir(exist_ok=True)

for table in TABLES:
    data = sb.table(table).select("*").order("id").execute().data
    path = out / f"{table}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{table}: {len(data)} rows -> {path}")
