# Hermes OS Dashboard v2.0

Bảng điều khiển trực quan (Streamlit + Supabase) cho hệ điều hành cá nhân **Hermes OS — "Bác Sĩ Chính Mình"**. Chuyển mô hình vận hành từ dòng lệnh sang một buồng lái duy nhất: theo dõi chi phí AI, điều phối đội agent, và quản trị cơ sở tri thức Obsidian Vault.

## Tính năng

- **Memory — Obsidian Vault**: liệt kê ghi chú `.md` từ Supabase dưới dạng thẻ kính (glassmorphism), lọc theo `Recent / Notes / Omi`, tìm kiếm theo tên.
- **Agents** (Claude / OpenClaw / Hermes): avatar gradient riêng, click để mở panel chi phí từng agent.
- **AI Spend**: tổng chi phí USD, token, số lần gọi, biểu đồ chi phí theo model — đọc bằng `service_role` (dữ liệu nhạy cảm, không lộ cho `anon`).
- **Giao diện tối tím-indigo** + accent cyan, đồng bộ nguyên mẫu thiết kế.

## Kiến trúc

| Thành phần | Vai trò |
|---|---|
| `app.py` | Ứng dụng Streamlit: UI, điều hướng qua query param (`?nav=...`), 2 client Supabase (anon đọc công khai / service_role đọc nhạy cảm). |
| `security/00_full_setup.sql` | Tạo bảng (`obsidian_vault`, `ai_spend`, `mission_control`) + seed + RLS. Chạy 1 lần. |
| `security/rls_policies.sql` | Chỉ phần RLS (nếu bảng đã tồn tại). |
| `security/SECURITY.md` | Ghi chú bảo mật & checklist. |
| `shoot.py` | Chụp ảnh verify giao diện bằng Playwright. |

## Bảo mật

- **Không hardcode key** — đọc qua `st.secrets`. File `.streamlit/secrets.toml` nằm trong `.gitignore`.
- **RLS bật** trên cả 3 bảng. `anon` chỉ đọc `obsidian_vault` + `mission_control`; **không** đọc/ghi `ai_spend`.
- **service_role** chỉ dùng server-side (Streamlit server, n8n). Không bao giờ nhúng vào client JS.
- Giá trị tệp được `html.escape()` trước khi render (chống XSS).

## Cài đặt & chạy

1. Cài phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
2. Tạo cấu hình từ mẫu rồi điền key thật:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
   Lấy key tại Supabase → **Settings → API** (`URL`, `anon`, `service_role`).
3. Khởi tạo cơ sở dữ liệu: mở Supabase → **SQL Editor** → dán `security/00_full_setup.sql` → **Run**.
4. Chạy app:
   ```bash
   streamlit run app.py
   ```
   Mặc định: http://localhost:8501

## Tích hợp chi phí (tùy chọn)

Tại điểm cuối mỗi luồng gọi LLM (n8n), đẩy token tiêu hao về bảng `ai_spend` bằng **HTTP Request Node** dùng **service_role key** (lưu trong n8n Credentials). Hướng dẫn từng bước (credential, tính cost, node, test, troubleshoot): [`docs/n8n-ai-spend.md`](docs/n8n-ai-spend.md).

## Git Robot — sao lưu tự động

`.github/workflows/daily-backup.yml` chạy 00:00 giờ VN hằng ngày (hoặc bấm tay qua
**Actions → Run workflow**): export 3 bảng Supabase ra `backups/*.json` rồi commit về repo.

Cần thêm 2 secrets tại **Settings → Secrets and variables → Actions**:

| Secret | Giá trị |
|---|---|
| `SUPABASE_URL` | URL project Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | service_role key (đọc cả `ai_spend`) |

## Verify giao diện

```bash
pip install playwright && playwright install chromium
python shoot.py   # tạo shot_memory.png, shot_openclaw.png, ...
```

---

> ⚠️ Trước khi public repo hoặc chia sẻ: kiểm tra `secrets.toml` không bị commit (`git check-ignore .streamlit/secrets.toml`).

## License

[MIT](LICENSE) © 2026 Tuanphan1175
