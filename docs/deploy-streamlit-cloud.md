# Deploy lên Streamlit Community Cloud

Streamlit Cloud là nền tảng native cho app Streamlit: free, nối thẳng GitHub repo,
tự build lại mỗi lần push, có chỗ nhập Secrets an toàn. (Vercel KHÔNG hợp Streamlit
vì serverless không giữ được server + websocket.)

## Yêu cầu

- Repo GitHub: `Tuanphan1175/agent-hermes-os` (đã có).
- File entry: `app.py` (gốc repo).
- `requirements.txt` chỉ chứa dependency runtime (streamlit, pandas, supabase).
- Tài khoản Streamlit Cloud — đăng nhập bằng chính GitHub.

## Các bước

1. Vào **https://share.streamlit.io** → **Sign in with GitHub** → cấp quyền đọc repo.
2. **Create app → Deploy a public app from GitHub** (repo private vẫn deploy được sau khi cấp quyền).
3. Điền:
   - Repository: `Tuanphan1175/agent-hermes-os`
   - Branch: `main`
   - Main file path: `app.py`
   - (Advanced) Python version: **3.12**
4. Mở **Advanced settings → Secrets**, dán đúng định dạng TOML (giống `.streamlit/secrets.toml`):
   ```toml
   SUPABASE_URL = "https://<project-id>.supabase.co"
   SUPABASE_ANON_KEY = "<anon key>"
   SUPABASE_SERVICE_ROLE_KEY = "<service_role key>"
   ```
5. **Deploy**. Vài phút sau app chạy tại `https://<tên-app>.streamlit.app`.

## Sau deploy

- Mỗi `git push` lên `main` → Streamlit Cloud tự build lại.
- Cập nhật Secrets: **Manage app → Settings → Secrets** (không sửa trong repo).
- Xem log build/runtime: **Manage app → Logs**.

## Lưu ý bảo mật

- Secrets nhập trên Streamlit Cloud chạy server-side, không lộ ra trình duyệt.
- `service_role` chỉ nằm trong Secrets của Cloud — không commit vào repo.
- App đọc `obsidian_vault`/`mission_control` bằng anon (RLS cho phép), `ai_spend` bằng service_role.

## Lỗi thường gặp

| Triệu chứng | Khắc phục |
|---|---|
| `ModuleNotFoundError` | thiếu package trong `requirements.txt` |
| `KeyError: 'SUPABASE_URL'` | chưa nhập Secrets, hoặc sai tên khóa |
| App trắng / "chờ đồng bộ" | URL/anon key sai, hoặc chưa chạy `security/00_full_setup.sql` |
| Panel AI Spend cảnh báo | thiếu `SUPABASE_SERVICE_ROLE_KEY` trong Secrets |
| Build lỗi version Python | chọn Python 3.12 ở Advanced settings |
