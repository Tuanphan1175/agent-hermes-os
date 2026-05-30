# Hermes OS — Ghi chú bảo mật

Vá 3 lỗ hổng trong tài liệu v2.0.

## 1. Key hardcode trong `app.py`  →  ĐÃ SỬA
- Trước: `SUPABASE_KEY = "your-anon-key"` nằm thẳng trong mã, commit lên Git.
- Sau: đọc qua `st.secrets[...]`. Giá trị thật nằm ở `.streamlit/secrets.toml` (đã đưa vào `.gitignore`).
- Trên Streamlit Cloud: nhập tại **Settings → Secrets**, không đụng vào repo.

## 2. anon key dùng để GHI `ai_spend` qua n8n  →  ĐÃ SỬA
- Trước: n8n gắn **anon key** vào header để POST. Anon key là khóa công khai → ai có nó cũng ghi/đọc được bảng.
- Sau:
  - Bật **RLS** trên cả 3 bảng (`security/rls_policies.sql`).
  - n8n ghi bằng **service_role key** (server-side, không lộ ra trình duyệt). service_role tự bỏ qua RLS.
  - Lưu service_role trong **n8n Credentials**, KHÔNG ghi plaintext trong node.

### Cấu hình lại HTTP Request Node (n8n)
```
Method: POST
URL: https://your-project-id.supabase.co/rest/v1/ai_spend
Headers:
  apikey:        {{ $credentials.supabaseServiceRole }}
  Authorization: Bearer {{ $credentials.supabaseServiceRole }}
  Content-Type:  application/json
  Prefer:        return=minimal
Body (JSON): { model_name, input_tokens, output_tokens, cost_usd }
```

## 3. ai_spend đọc công khai  →  ĐÃ SỬA
- Chi phí là dữ liệu nhạy cảm. RLS **không** mở `SELECT` cho anon.
- Dashboard đọc chi phí qua client **service_role riêng** (`get_admin_client()` trong `app.py`,
  cache bằng `@st.cache_resource`), tách hẳn khỏi client anon. Key lấy từ
  `st.secrets["SUPABASE_SERVICE_ROLE_KEY"]` — chỉ tồn tại server-side.
- Panel "AI Spend": tổng chi phí, tổng token, số lần gọi, biểu đồ chi phí theo model, bảng chi tiết.
- Không có key service_role -> panel hiện cảnh báo, KHÔNG fallback sang anon.

## Lỗi phụ đã vá trong `app.py`
- f-string thẻ card dùng `{{row[...]}}` (hai ngoặc) → render ra chữ literal `{row['file_name']}` thay vì giá trị. Sửa còn một ngoặc.
- Thêm `html.escape()` cho tên/đường dẫn tệp trước khi nhúng HTML → chống XSS qua tên tệp.
- `str.contains(..., regex=False)` → tránh lỗi khi người dùng gõ ký tự regex.

## Việc cần làm thủ công
- [ ] Xoay (rotate) anon key cũ nếu đã từng commit lên Git công khai.
- [ ] Chạy `security/rls_policies.sql` trên Supabase.
- [ ] Chuyển n8n sang service_role credential.
- [ ] Điền key thật vào `.streamlit/secrets.toml` (local) hoặc Streamlit Cloud Secrets.
