-- =====================================================================
-- Hermes OS — Full setup. Paste TOÀN BỘ vào Supabase SQL Editor -> Run.
-- Gồm: tạo bảng + seed obsidian_vault + bật RLS.
-- =====================================================================

-- 1) SCHEMA -----------------------------------------------------------
DROP TABLE IF EXISTS obsidian_vault;
DROP TABLE IF EXISTS ai_spend;
DROP TABLE IF EXISTS mission_control;

CREATE TABLE obsidian_vault (
    id SERIAL PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    category TEXT DEFAULT 'Recent',
    updated_at TEXT NOT NULL
);

CREATE TABLE ai_spend (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    model_name TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd NUMERIC(10, 6) NOT NULL
);

CREATE TABLE mission_control (
    id SERIAL PRIMARY KEY,
    goal_name TEXT NOT NULL,
    status TEXT DEFAULT 'To Do',
    turn_budget INTEGER DEFAULT 20,
    turns_used INTEGER DEFAULT 0,
    progress_percent INTEGER DEFAULT 0
);

-- 2) SEED obsidian_vault ---------------------------------------------
INSERT INTO obsidian_vault (file_name, file_path, category, updated_at) VALUES
('2026-05-18', 'Agentic OS/Memories/2026-05-18.md', 'Recent', '15m ago'),
('Memories', 'Omi/Memories.md', 'Recent', '24m ago'),
('Goals', 'Agentic OS/Goals.md', 'Recent', '37m ago'),
('2026-05-17', 'Agentic OS/Memories/2026-05-17.md', 'Recent', '23h ago'),
('Build Your Own', 'Agentic OS/Build Your Own.md', 'Recent', '1d ago'),
('2026-05-16', 'Agentic OS/Memories/2025-05-16.md', 'Recent', '1d ago'),
('2026-05-16', '01 Daily/2026-05-16.md', 'Notes', '2d ago'),
('2026-05-16', 'Agentic OS/Journal/2025-05-16.md', 'Recent', '2d ago'),
('SEO-Brief-FreeAIAgents-2026-05-13', '04 Resources/SEO Briefs/SEO-Brief-FreeAIAgents-2026-05-13.md', 'Recent', '2d ago');

-- 3) (tùy chọn) seed ai_spend để thấy panel chi phí ngay -------------
INSERT INTO ai_spend (model_name, input_tokens, output_tokens, cost_usd) VALUES
('claude-opus-4-8', 12000, 3400, 0.285000),
('claude-sonnet-4-6', 45000, 8200, 0.159600),
('claude-haiku-4-5', 90000, 15000, 0.097500);

-- 3b) (tùy chọn) seed mission_control để thấy panel ngay --------------
INSERT INTO mission_control (goal_name, status, turn_budget, turns_used, progress_percent) VALUES
('Ra mắt landing page Free AI Agents', 'In Progress', 30, 18, 60),
('Tự động hóa SEO brief hằng tuần',    'To Do',       20,  0,  0),
('Backup bộ não Hermes lên Git',       'Done',        10,  9, 100),
('Tích hợp n8n đo chi phí token',      'In Progress', 25, 12, 45);

-- 4) RLS --------------------------------------------------------------
ALTER TABLE obsidian_vault  ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_spend        ENABLE ROW LEVEL SECURITY;
ALTER TABLE mission_control ENABLE ROW LEVEL SECURITY;

REVOKE INSERT, UPDATE, DELETE ON obsidian_vault  FROM anon;
REVOKE INSERT, UPDATE, DELETE ON ai_spend        FROM anon;
REVOKE INSERT, UPDATE, DELETE ON mission_control FROM anon;

DROP POLICY IF EXISTS "vault_read_anon" ON obsidian_vault;
CREATE POLICY "vault_read_anon" ON obsidian_vault
    FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "mission_read_anon" ON mission_control;
CREATE POLICY "mission_read_anon" ON mission_control
    FOR SELECT TO anon USING (true);

-- ai_spend: cố ý KHÔNG có policy cho anon -> anon bị chặn đọc/ghi.
-- Dashboard đọc ai_spend bằng service_role (bỏ qua RLS).
