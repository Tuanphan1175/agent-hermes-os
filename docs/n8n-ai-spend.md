# Hướng dẫn n8n — Đẩy chi phí token về `ai_spend`

Mục tiêu: tại điểm cuối mỗi luồng gọi LLM trong n8n, ghi 1 dòng vào bảng `ai_spend`
của Supabase (model, token vào/ra, chi phí USD). Dashboard sẽ tự tổng hợp.

```
[LLM node] -> [Function: tính cost] -> [HTTP Request: POST ai_spend]
```

---

## 1. Chuẩn bị

- Project Supabase đã chạy `security/00_full_setup.sql` (có bảng `ai_spend`).
- `service_role` key (Supabase → Settings → API). Dùng service_role vì RLS chặn `anon` ghi/đọc `ai_spend`.
- n8n bản cloud hoặc self-host, có quyền tạo workflow.

> ⚠️ service_role bỏ qua mọi RLS. Chỉ đặt trong n8n Credentials (mã hóa), KHÔNG dán
> thẳng vào node, KHÔNG log ra ngoài.

---

## 2. Tạo Credential (1 lần)

n8n → **Credentials → New → Header Auth** (hoặc Generic Credential):

| Field | Giá trị |
|---|---|
| Name | `Supabase service_role` |
| Header Name | `Authorization` |
| Header Value | `Bearer <SERVICE_ROLE_KEY>` |

Supabase REST cần thêm header `apikey`. Có 2 cách:
- Đặt `apikey` trực tiếp trong node (giá trị = service_role key), hoặc
- Dùng credential thứ hai. Đơn giản nhất: để `Authorization` trong credential, `apikey` đặt ở node.

---

## 3. Node tính chi phí (Function / Code)

Đặt **Code node** trước HTTP Request để chuẩn hóa dữ liệu. Ví dụ (JavaScript):

```javascript
// Bảng giá USD / 1 triệu token (cập nhật theo model thực tế)
const PRICES = {
  "claude-opus-4-8":   { in: 15.00, out: 75.00 },
  "claude-sonnet-4-6": { in: 3.00,  out: 15.00 },
  "claude-haiku-4-5":  { in: 0.80,  out: 4.00  },
};

const model = $json.model || "claude-sonnet-4-6";
const inTok  = Number($json.usage?.input_tokens  ?? $json.input_tokens  ?? 0);
const outTok = Number($json.usage?.output_tokens ?? $json.output_tokens ?? 0);

const p = PRICES[model] || { in: 0, out: 0 };
const cost = (inTok / 1e6) * p.in + (outTok / 1e6) * p.out;

return [{
  json: {
    model_name: model,
    input_tokens: inTok,
    output_tokens: outTok,
    cost_usd: Number(cost.toFixed(6)),
  },
}];
```

> Lưu ý: `model_name` nên chứa tên agent (vd `claude-...`, `openclaw-...`, `hermes-...`)
> để panel agent trên dashboard lọc đúng (nó dùng `ilike '%<agent>%'`).

---

## 4. HTTP Request Node — POST vào Supabase

| Tham số | Giá trị |
|---|---|
| Method | `POST` |
| URL | `https://<project-id>.supabase.co/rest/v1/ai_spend` |
| Authentication | Header Auth credential `Supabase service_role` |
| Send Headers | bật |
| Send Body | bật, dạng **JSON** |

Headers (thêm thủ công nếu credential chưa có):

| Key | Value |
|---|---|
| `apikey` | `<SERVICE_ROLE_KEY>` |
| `Content-Type` | `application/json` |
| `Prefer` | `return=minimal` |

Body (JSON) — map từ Code node:

```json
{
  "model_name": "={{ $json.model_name }}",
  "input_tokens": "={{ $json.input_tokens }}",
  "output_tokens": "={{ $json.output_tokens }}",
  "cost_usd": "={{ $json.cost_usd }}"
}
```

PostgREST tự gán `id` (serial) và `created_at` (default now), không cần gửi.

---

## 5. Test

1. Chạy workflow tay (Execute Workflow) với 1 LLM call mẫu.
2. HTTP Request trả **HTTP 201** = ghi thành công.
3. Kiểm tra Supabase → Table Editor → `ai_spend` có dòng mới.
4. Mở dashboard → panel **AI Spend** và panel agent tương ứng → số cập nhật.

Kiểm tra nhanh bằng curl (thay key + url):

```bash
curl -X POST "https://<project-id>.supabase.co/rest/v1/ai_spend" \
  -H "apikey: <SERVICE_ROLE_KEY>" \
  -H "Authorization: Bearer <SERVICE_ROLE_KEY>" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d '{"model_name":"claude-sonnet-4-6","input_tokens":1000,"output_tokens":300,"cost_usd":0.0075}'
```

---

## 6. Lỗi thường gặp

| Triệu chứng | Nguyên nhân | Khắc phục |
|---|---|---|
| `401 Unauthorized` | thiếu/sai `apikey` hoặc `Authorization` | đủ cả 2 header, đúng service_role key |
| `404` / `PGRST205` | bảng `ai_spend` chưa tồn tại | chạy `security/00_full_setup.sql` |
| `400` | kiểu dữ liệu sai (token là chuỗi) | ép số trong Code node (`Number(...)`) |
| Ghi được nhưng dashboard trống | dashboard đọc bằng service_role, key sai/thiếu | kiểm tra `SUPABASE_SERVICE_ROLE_KEY` trong `secrets.toml` |
| `42501 RLS` khi dùng anon | dùng nhầm anon key để ghi | bắt buộc service_role cho `ai_spend` |

---

## 7. Bảo mật

- service_role chỉ sống trong n8n Credentials và GitHub Actions secrets — không vào repo, không vào client.
- Nếu key lộ: Supabase → Settings → API → **Reset** service_role, cập nhật lại n8n + secrets.
- Cân nhắc tách 1 Postgres role ghi-chỉ-`ai_spend` thay vì service_role toàn quyền (nâng cao).
