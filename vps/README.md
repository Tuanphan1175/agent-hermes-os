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

## 4. Expose ra internet

> **Triển khai thực tế** dùng **Nginx Proxy Manager** (Docker `jc21/nginx-proxy-manager`, giữ 80/443) → `https://hermes-api.tuandoctor.com`. NPM chạy trong container nên **không** với tới `127.0.0.1` của host. Sửa shim bind gateway docker của NPM:
>
> ```bash
> # lấy gateway mạng NPM
> docker network inspect $(docker inspect nginx-proxy-manager \
>   -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}') \
>   -f '{{(index .IPAM.Config 0).Gateway}}'    # vd 172.26.0.1
> ```
>
> Đổi `ExecStart` trong unit: `--host 127.0.0.1` → `--host <gateway>` (vd `172.26.0.1`), `daemon-reload` + restart.
> Trong NPM UI (cổng 81): **Add Proxy Host** → domain `hermes-api.tuandoctor.com`, scheme `http`, forward `<gateway>:9100`, tab SSL **Request a new Certificate** + Force SSL. Nếu DNS proxy qua Cloudflare (orange) làm fail HTTP-01 challenge → tắt proxy CF (xám mây) khi xin cert, hoặc dùng DNS Challenge.

Cách khác (không Docker): Cloudflare Tunnel `cloudflared tunnel --url http://localhost:9100`, hoặc reverse proxy host nginx/caddy trỏ subdomain → `127.0.0.1:9100` (giữ bind `127.0.0.1`).

## 5. Cấu hình dashboard

Trên Streamlit Cloud → **Settings → Secrets**, thêm:

```toml
HERMES_API_URL = "https://hermes-api.tuandoctor.com"
HERMES_API_KEY = "<đúng key ở bước 2>"
```

Mở app → agent **Hermes** → khung chat "Chat với Hermes (thật)" hiện ra.

## Ép model theo request (Model Arena)

`/chat` nhận thêm field tùy chọn `model`. Khi có, shim chạy
`hermes chat --model <model> -q "<msg>"` để **ép đúng model** thay vì để Hermes tự
định tuyến. Dùng cho tab **Workspace → So sánh Model** (các cột "· Hermes").

- Cờ `--model` theo CLI [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent).
  Nếu bản của bạn khác, đổi qua env `HERMES_MODEL_FLAG` (vd `-m`).
  Kiểm tra: `hermes chat --help` và `hermes model` (liệt kê model đã cấu hình).
- `model` phải khớp id model trong cấu hình Hermes của bạn (có thể cần tiền tố vendor,
  vd `openai/gpt-5.5`). Id mặc định app gửi = cột `model` trong `HERMES_MODELS` (app.py):
  `gpt-5.5`, `deepseek-4-flash`, `minimax-m3` — sửa ở đó nếu CLI dùng id khác.
- Bỏ trống `model` ⇒ giữ nguyên hành vi cũ (Hermes auto-route). **Tương thích ngược**:
  shim cũ (chưa cập nhật) bỏ qua field `model`, không lỗi.

Test ép model trên VPS:

```bash
curl -s -X POST localhost:9100/chat \
  -H "Authorization: Bearer <HERMES_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Bạn là model nào?","model":"deepseek-4-flash"}'
```

Deploy bản mới: copy `hermes_api.py` mới lên VPS rồi `systemctl --user restart hermes-api`.

## Bảo mật

- Key chỉ nằm trong `hermes-api.env` (VPS) + Streamlit Secrets — KHÔNG vào repo.
- Shim chống shell-injection (subprocess arg list, không `shell=True`).
- Auth Bearer so sánh hằng-thời-gian.
- Shim bind gateway docker NPM (`172.26.0.1`), không phơi ra internet trực tiếp; TLS do NPM (Let's Encrypt) đảm nhiệm tại biên.
- ⚠️ Đổi (rotate) key nếu nghi lộ; cập nhật cả env VPS lẫn Streamlit Secrets.
