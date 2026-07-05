import sqlite3
import json
import os
import sys
from pathlib import Path

# Console Windows mặc định cp1252 không in được ký tự Unicode -> ép UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Paths
DB_PATH = Path(__file__).resolve().parent / "hermes_os.db"
BACKUPS_DIR = Path(__file__).resolve().parent / "backups"

def init_db():
    """Khởi tạo cơ sở dữ liệu SQLite cục bộ và nạp dữ liệu từ file backup hoặc mặc định."""
    db_existed = DB_PATH.exists()
    
    # Kết nối tạo DB mới nếu chưa tồn tại
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 1) Tạo cấu trúc các bảng giống Supabase
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS obsidian_vault (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        category TEXT DEFAULT 'Recent',
        updated_at TEXT NOT NULL,
        links TEXT NOT NULL DEFAULT '[]'
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_spend (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        model_name TEXT NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        cost_usd REAL NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mission_control (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_name TEXT NOT NULL,
        status TEXT DEFAULT 'To Do',
        turn_budget INTEGER DEFAULT 20,
        turns_used INTEGER DEFAULT 0,
        progress_percent INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notebook (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL DEFAULT 'Untitled',
        content TEXT NOT NULL DEFAULT '',
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entry_date TEXT NOT NULL DEFAULT CURRENT_DATE,
        content TEXT NOT NULL DEFAULT '',
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ideas (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        source TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS datastore (
        key TEXT PRIMARY KEY,
        data TEXT NOT NULL DEFAULT '[]'
    )
    """)
    
    conn.commit()

    # 2) Seeding dữ liệu nếu DB vừa được tạo mới
    if not db_existed:
        print("[local_db] Đang khởi tạo cơ sở dữ liệu mới hermes_os.db...")
        
        # Hàm trợ giúp nạp dữ liệu từ file backup JSON
        def load_backup(filename):
            path = BACKUPS_DIR / filename
            if path.exists() and path.stat().st_size > 5:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data and isinstance(data, list):
                            return data
                except Exception as e:
                    print(f"[local_db] Lỗi khi đọc file backup {filename}: {e}")
            return None

        # --- SEED obsidian_vault ---
        vault_data = load_backup("obsidian_vault.json")
        if vault_data:
            for row in vault_data:
                links_str = json.dumps(row.get("links", []))
                cursor.execute(
                    "INSERT INTO obsidian_vault (file_name, file_path, category, updated_at, links) VALUES (?, ?, ?, ?, ?)",
                    (row["file_name"], row["file_path"], row.get("category", "Recent"), row["updated_at"], links_str)
                )
            print(f"[local_db] Đã nạp {len(vault_data)} ghi chú từ obsidian_vault.json backup.")
        else:
            vault_seeds = [
                ('2026-05-18', 'Agentic OS/Memories/2026-05-18.md', 'Recent', '15m ago', '[]'),
                ('Memories', 'Omi/Memories.md', 'Recent', '24m ago', '[]'),
                ('Goals', 'Agentic OS/Goals.md', 'Recent', '37m ago', '[]'),
                ('2026-05-17', 'Agentic OS/Memories/2026-05-17.md', 'Recent', '23h ago', '[]'),
                ('Build Your Own', 'Agentic OS/Build Your Own.md', 'Recent', '1d ago', '[]'),
                ('2026-05-16', 'Agentic OS/Memories/2025-05-16.md', 'Recent', '1d ago', '[]'),
                ('2026-05-16', '01 Daily/2026-05-16.md', 'Notes', '2d ago', '[]'),
                ('2026-05-16', 'Agentic OS/Journal/2025-05-16.md', 'Recent', '2d ago', '[]'),
                ('SEO-Brief-FreeAIAgents-2026-05-13', '04 Resources/SEO Briefs/SEO-Brief-FreeAIAgents-2026-05-13.md', 'Recent', '2d ago', '[]')
            ]
            cursor.executemany("INSERT INTO obsidian_vault (file_name, file_path, category, updated_at, links) VALUES (?, ?, ?, ?, ?)", vault_seeds)

        # --- SEED ai_spend ---
        spend_data = load_backup("ai_spend.json")
        if spend_data:
            for row in spend_data:
                cursor.execute(
                    "INSERT INTO ai_spend (created_at, model_name, input_tokens, output_tokens, cost_usd) VALUES (?, ?, ?, ?, ?)",
                    (row.get("created_at"), row["model_name"], row["input_tokens"], row["output_tokens"], row["cost_usd"])
                )
            print(f"[local_db] Đã nạp {len(spend_data)} bản ghi chi phí từ ai_spend.json backup.")
        else:
            spend_seeds = [
                ('claude-opus-4-8', 12000, 3400, 0.285000),
                ('claude-sonnet-4-6', 45000, 8200, 0.159600),
                ('claude-haiku-4-5', 90000, 15000, 0.097500)
            ]
            for s in spend_seeds:
                cursor.execute("INSERT INTO ai_spend (model_name, input_tokens, output_tokens, cost_usd) VALUES (?, ?, ?, ?)", s)

        # --- SEED mission_control ---
        mc_data = load_backup("mission_control.json")
        if mc_data:
            for row in mc_data:
                cursor.execute(
                    "INSERT INTO mission_control (goal_name, status, turn_budget, turns_used, progress_percent) VALUES (?, ?, ?, ?, ?)",
                    (row["goal_name"], row.get("status", "To Do"), row.get("turn_budget", 20), row.get("turns_used", 0), row.get("progress_percent", 0))
                )
            print(f"[local_db] Đã nạp {len(mc_data)} mục tiêu từ mission_control.json backup.")
        else:
            mc_seeds = [
                ('Ra mắt landing page Free AI Agents', 'In Progress', 30, 18, 60),
                ('Tự động hóa SEO brief hằng tuần',    'To Do',       20,  0,  0),
                ('Backup bộ não Hermes lên Git',       'Done',        10,  9, 100),
                ('Tích hợp n8n đo chi phí token',      'In Progress', 25, 12, 45)
            ]
            cursor.executemany("INSERT INTO mission_control (goal_name, status, turn_budget, turns_used, progress_percent) VALUES (?, ?, ?, ?, ?)", mc_seeds)

        # --- SEED ideas ---
        ideas_data = load_backup("ideas.json")
        if ideas_data:
            for row in ideas_data:
                cursor.execute(
                    "INSERT INTO ideas (id, title, description, category, source, status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (row["id"], row["title"], row.get("description"), row["category"], row["source"], row.get("status", "pending"), row.get("timestamp"))
                )
            print(f"[local_db] Đã nạp {len(ideas_data)} ý tưởng từ ideas.json backup.")
        else:
            idea_seeds = [
                ('idea-1', 'Auto-sync Obsidian with Telegram Agent', 'Trigger an alert on Telegram whenever a new note is added to the vault.', 'Experiment', 'sage', 'pending'),
                ('idea-2', 'Build a custom n8n dashboard for token cost tracking', 'Render a bar chart of everyday model expenses with direct API calls.', 'Build', 'max', 'approved'),
                ('idea-3', 'Create a 5-minute video tutorial explaining OpenClaw setup', 'High-retention script outline demonstrating local swarm coordination.', 'Content', 'nova', 'pending')
            ]
            cursor.executemany("INSERT INTO ideas (id, title, description, category, source, status) VALUES (?, ?, ?, ?, ?, ?)", idea_seeds)

        # --- SEED datastore (youtube-scripts, seo-campaigns, seo-transcripts) ---
        # YouTube Scripts
        yt_data = load_backup("youtube_scripts.json")
        if not yt_data:
            yt_data = [
              {
                "id": "script-1",
                "title": "How To Build a Public Scoreboard for 7 AI Agents in OpenClaw",
                "hook": False,
                "outline": True,
                "fullScript": False,
                "status": "pending_review",
                "category": "ideas",
                "type": "articles",
                "notes": ""
              },
              {
                "id": "script-2",
                "title": "How To Run OpenClaw With Claude and Gemma 4 for $30/Month",
                "hook": True,
                "outline": True,
                "fullScript": True,
                "status": "pending_review",
                "category": "ideas",
                "type": "videos",
                "notes": ""
              }
            ]
        cursor.execute("INSERT INTO datastore (key, data) VALUES (?, ?)", ("youtube-scripts", json.dumps(yt_data)))

        # SEO Campaigns
        seo_camp = load_backup("seo_campaigns.json")
        if seo_camp:
            cursor.execute("INSERT INTO datastore (key, data) VALUES (?, ?)", ("seo-campaigns", json.dumps(seo_camp)))
        else:
            cursor.execute("INSERT INTO datastore (key, data) VALUES (?, ?)", ("seo-campaigns", json.dumps([])))

        # SEO Transcripts
        seo_trans = load_backup("seo_transcripts.json")
        if seo_trans:
            cursor.execute("INSERT INTO datastore (key, data) VALUES (?, ?)", ("seo-transcripts", json.dumps(seo_trans)))
        else:
            cursor.execute("INSERT INTO datastore (key, data) VALUES (?, ?)", ("seo-transcripts", json.dumps([])))
            
        conn.commit()
    conn.close()


# Initialize the database immediately
init_db()


class ExecuteResult:
    def __init__(self, data):
        self.data = data


class QueryBuilder:
    def __init__(self, table_name):
        # Đồng bộ hóa tên bảng (hỗ trợ cả hoa, thường và số nhiều/ít)
        t = table_name.lower()
        if t == "idea":
            t = "ideas"
        elif t == "datastore":
            t = "datastore"
        self.table = t
        
        self.select_cols = "*"
        self.filters = []
        self.order_by = None
        self.limit_val = None
        self.is_delete = False
        self.update_data = None
        self.insert_data = None

    def select(self, cols="*"):
        self.select_cols = cols
        return self

    def eq(self, column, value):
        self.filters.append((column, "=", value))
        return self

    def neq(self, column, value):
        self.filters.append((column, "!=", value))
        return self

    def order(self, column, desc=False):
        self.order_by = (column, "DESC" if desc else "ASC")
        return self

    def limit(self, limit_val):
        self.limit_val = limit_val
        return self

    def delete(self):
        self.is_delete = True
        return self

    def update(self, data):
        self.update_data = data
        return self

    def insert(self, data):
        self.insert_data = data
        return self

    def execute(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        def parse_row(row):
            d = dict(row)
            # Tự động parse JSON của cột 'links' và 'data'
            for col in ['links', 'data']:
                if col in d and isinstance(d[col], str):
                    try:
                        d[col] = json.loads(d[col])
                    except Exception:
                        pass
            return d

        params = []

        # 1) Xử lý INSERT
        if self.insert_data is not None:
            if isinstance(self.insert_data, list):
                rows_to_insert = self.insert_data
            else:
                rows_to_insert = [self.insert_data]
            
            inserted_rows = []
            for row in rows_to_insert:
                row_copy = row.copy()
                for col in ['links', 'data']:
                    if col in row_copy and not isinstance(row_copy[col], str):
                        row_copy[col] = json.dumps(row_copy[col])
                
                cols = list(row_copy.keys())
                vals = list(row_copy.values())
                placeholders = ", ".join(["?"] * len(cols))
                
                sql_insert = f"INSERT INTO {self.table} ({', '.join(cols)}) VALUES ({placeholders})"
                cursor.execute(sql_insert, vals)
                
                last_id = cursor.lastrowid
                if last_id and self.table != 'ideas' and self.table != 'datastore':
                    # Trả về bản ghi vừa tạo
                    cursor.execute(f"SELECT * FROM {self.table} WHERE rowid = ?", (last_id,))
                    new_row = cursor.fetchone()
                    if new_row:
                        inserted_rows.append(parse_row(new_row))
                    else:
                        inserted_rows.append(row)
                else:
                    inserted_rows.append(row)
            
            conn.commit()
            conn.close()
            return ExecuteResult(inserted_rows)

        # 2) Xử lý UPDATE
        elif self.update_data is not None:
            data_copy = self.update_data.copy()
            for col in ['links', 'data']:
                if col in data_copy and not isinstance(data_copy[col], str):
                    data_copy[col] = json.dumps(data_copy[col])

            set_parts = []
            for col, val in data_copy.items():
                set_parts.append(f"{col} = ?")
                params.append(val)
            
            where_parts = []
            for col, op, val in self.filters:
                where_parts.append(f"{col} {op} ?")
                params.append(val)
            
            where_clause = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
            sql_update = f"UPDATE {self.table} SET {', '.join(set_parts)}{where_clause}"
            cursor.execute(sql_update, params)
            conn.commit()
            
            # Lấy các hàng đã cập nhật để trả về giống Supabase
            where_params = [val for _, _, val in self.filters]
            sql_select = f"SELECT * FROM {self.table}{where_clause}"
            cursor.execute(sql_select, where_params)
            updated_rows = [parse_row(r) for r in cursor.fetchall()]
            conn.close()
            return ExecuteResult(updated_rows)

        # 3) Xử lý DELETE
        elif self.is_delete:
            where_parts = []
            for col, op, val in self.filters:
                where_parts.append(f"{col} {op} ?")
                params.append(val)
            
            where_clause = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
            sql_delete = f"DELETE FROM {self.table}{where_clause}"
            cursor.execute(sql_delete, params)
            conn.commit()
            conn.close()
            return ExecuteResult([])

        # 4) Xử lý SELECT
        else:
            where_parts = []
            for col, op, val in self.filters:
                where_parts.append(f"{col} {op} ?")
                params.append(val)
            
            where_clause = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""
            
            order_clause = ""
            if self.order_by:
                col, dir = self.order_by
                order_clause = f" ORDER BY {col} {dir}"
                
            limit_clause = f" LIMIT {self.limit_val}" if self.limit_val is not None else ""
            
            sql_select = f"SELECT {self.select_cols} FROM {self.table}{where_clause}{order_clause}{limit_clause}"
            cursor.execute(sql_select, params)
            rows = cursor.fetchall()
            
            res_data = [parse_row(r) for r in rows]
            conn.close()
            return ExecuteResult(res_data)


class LocalSupabaseClient:
    def table(self, table_name):
        return QueryBuilder(table_name)
    
    def from_(self, table_name):
        return QueryBuilder(table_name)


# Mock clients
supabase = LocalSupabaseClient()

def get_admin_client() -> LocalSupabaseClient | None:
    # Do chạy local offline không cần quan tâm key service_role nữa,
    # trả về thẳng client local để render đầy đủ thông tin AI Spend.
    return supabase
