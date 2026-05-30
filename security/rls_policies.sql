-- =====================================================================
-- Hermes OS — Row Level Security (RLS) hardening
-- Chạy SAU khi đã tạo bảng (Chương 1). Áp dụng tại Supabase SQL Editor.
--
-- Nguyên tắc:
--   * anon key (lộ phía client)  -> CHỈ đọc, không ghi.
--   * service_role key (server)  -> tự động bỏ qua RLS, dùng cho n8n ghi ai_spend.
-- =====================================================================

-- 1. Bật RLS cho cả 3 bảng. Khi bật mà chưa có policy => mặc định CHẶN hết.
ALTER TABLE obsidian_vault  ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_spend        ENABLE ROW LEVEL SECURITY;
ALTER TABLE mission_control ENABLE ROW LEVEL SECURITY;

-- 2. Thu hồi mọi quyền ghi mặc định của vai trò anon.
REVOKE INSERT, UPDATE, DELETE ON obsidian_vault  FROM anon;
REVOKE INSERT, UPDATE, DELETE ON ai_spend        FROM anon;
REVOKE INSERT, UPDATE, DELETE ON mission_control FROM anon;

-- ---------------------------------------------------------------------
-- obsidian_vault: dashboard cần đọc danh sách ghi chú.
-- ---------------------------------------------------------------------
DROP POLICY IF EXISTS "vault_read_anon" ON obsidian_vault;
CREATE POLICY "vault_read_anon"
  ON obsidian_vault
  FOR SELECT
  TO anon
  USING (true);

-- ---------------------------------------------------------------------
-- ai_spend: anon KHÔNG đọc (chi phí là dữ liệu nhạy cảm), KHÔNG ghi.
-- Ghi do n8n thực hiện bằng service_role (bỏ qua RLS, không cần policy).
-- Đọc cho dashboard: chuyển sang truy vấn server-side bằng service_role,
-- KHÔNG mở SELECT cho anon. Nếu vẫn muốn anon đọc, mở policy bên dưới.
-- ---------------------------------------------------------------------
-- (cố ý KHÔNG có policy SELECT cho anon -> anon bị chặn đọc ai_spend)

-- ---------------------------------------------------------------------
-- mission_control: dashboard đọc tiến độ mục tiêu.
-- ---------------------------------------------------------------------
DROP POLICY IF EXISTS "mission_read_anon" ON mission_control;
CREATE POLICY "mission_read_anon"
  ON mission_control
  FOR SELECT
  TO anon
  USING (true);
