# Hermes API shim (VPS)

Dashboard không gọi thẳng được Hermes (Hermes chỉ có CLI + gateway messaging, không có
REST API). Shim này là 1 FastAPI nhỏ bọc `hermes chat -q`, để app POST `/chat` và nhận reply.

```
Streamlit app  --POST /chat {message} + Bearer-->  hermes_api.py (VPS)  --subprocess-->  hermes chat -q
               <--{reply}-------------------------                      <--stdout-------
```

## 1. Cài trên VPS

```bash
mkdir -p /root/hermes-api && cd /root/hermes-api
# copy hermes_api.py + requirements.txt vào đây (scp/git)
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
```

## 2. Tạo key + env

```bash
# sinh token ngẫu nhiên mạnh
openssl rand -hex 32      # copy chuỗi này làm HERMES_API_KEY

# file env (chmod 600, KHÔNG commit)
cat > /root/.hermes/hermes-api.env <<'EOF'
HERMES_API_KEY=<dán chuỗi vừa sinh>
HERMES_BIN=/root/.hermes/hermes-agent/venv/bin/hermes
HERMES_TIMEOUT=180
EOF
chmod 600 /root/.hermes/hermes-api.env
```

> `HERMES_BIN`: đường dẫn tuyệt đối tới lệnh `hermes` (kiểm tra bằng `which hermes`).

## 3. Chạy như service

```bash
cp hermes-api.service ~/.config/systemd/user/   # hoặc /etc/systemd/system nếu chạy system-wide
systemctl --user daemon-reload
systemctl --user enable --now hermes-api
systemctl --user status hermes-api
```

Test local trên VPS:

```bash
curl -s localhost:9100/health
curl -s -X POST localhost:9100/chat \
  -H "Authorization: Bearer <HERMES_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Xin chào Hermes"}'
```

## 4. Expose ra internet (Cloudflare)

Shim chỉ listen `127.0.0.1:9100`. Đưa ra ngoài qua **Cloudflare Tunnel** (khuyến nghị, không mở port):

```bash
cloudflared tunnel --url http://localhost:9100
# hoặc cấu hình named tunnel -> api-hermes.thsbsphananhtuan.com
```

Hoặc dùng reverse proxy (nginx/caddy) sẵn có, trỏ subdomain `api-hermes...` → `127.0.0.1:9100`.

## 5. Cấu hình dashboard

Trên Streamlit Cloud → **Settings → Secrets**, thêm:

```toml
HERMES_API_URL = "https://api-hermes.thsbsphananhtuan.com"
HERMES_API_KEY = "<đúng key ở bước 2>"
```

Mở app → agent **Hermes** → khung chat "Chat với Hermes (thật)" hiện ra.

## Bảo mật

- Key chỉ nằm trong `hermes-api.env` (VPS) + Streamlit Secrets — KHÔNG vào repo.
- Shim chống shell-injection (subprocess arg list, không `shell=True`).
- Auth Bearer so sánh hằng-thời-gian.
- Chỉ listen localhost; ra ngoài qua Cloudflare (TLS + có thể bật Access/WAF).
- ⚠️ Đổi (rotate) key nếu nghi lộ; cập nhật cả env VPS lẫn Streamlit Secrets.
