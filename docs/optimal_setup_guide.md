# Hướng dẫn Tối ưu hóa và Thiết lập Agentic OS Dashboard

Chào bạn! Dưới đây là hướng dẫn từng bước chi tiết để cấu hình và khai thác tối đa sức mạnh của hệ thống **Agentic OS Dashboard** (phiên bản chạy local hoặc đã deploy trên Streamlit Cloud). 

Hệ thống của bạn hiện đã được trang bị đầy đủ các kết nối quan trọng trong file [secrets.toml](file:///d:/B%C3%81C%20S%C4%A8%20CH%C3%8DNH%20M%C3%8CNH/Project/agent-hermes-os/.streamlit/secrets.toml) (Supabase, Netlify, Hermes API, Minimax API, Obsidian Vault Path). Để sử dụng tối ưu, hãy hoàn thiện các bước sau:

---

## 1. Đồng bộ dữ liệu Obsidian (Memory & Knowledge Graph)
Tab **Memory** và sơ đồ **D3 Knowledge Graph** hoạt động dựa trên các ghi chú y khoa trong Obsidian Vault của bạn được đẩy lên bảng `obsidian_vault` của Supabase.

### 🚩 Cách thực hiện:
1. **Chạy đồng bộ thủ công lần đầu:**
   Mở terminal (PowerShell) tại thư mục `agent-hermes-os` và chạy lệnh sau để kiểm tra dữ liệu trước (chế độ dry-run):
   ```powershell
   python scripts/sync_obsidian.py --vault "D:/BÁC SĨ CHÍNH MÌNH/Project/my-second-brain" --dry-run
   ```
   Nếu mọi thứ ổn định, chạy lệnh thực tế để đẩy toàn bộ ghi chú lên Supabase:
   ```powershell
   python scripts/sync_obsidian.py --vault "D:/BÁC SĨ CHÍNH MÌNH/Project/my-second-brain"
   ```

2. **Cài đặt đồng bộ tự động (Auto-sync mỗi 6 giờ):**
   Để dữ liệu tự động cập nhật mà không cần chạy tay, hãy đăng ký một tác vụ tự động trong Windows Task Scheduler:
   ```powershell
   python scripts/install_task.py
   ```
   *Lưu ý: Tác vụ này sẽ chạy file `scripts/run_sync.py` định kỳ để tự động đọc `OBSIDIAN_VAULT_PATH` từ file `secrets.toml`.*

---

## 2. Tối ưu hóa SEO Pipeline (Tự động hóa bài viết & Deploy Netlify)
Quy trình SEO Pipeline giúp bạn biến bản ghi âm Zoom/YouTube thành 5 bài viết chuẩn SEO và tự động deploy lên Netlify Funnels.

### 🚩 Cách sử dụng hiệu quả:
1. **Import Transcripts:** 
   * Truy cập tab **SEO Pipeline** -> chuyển sang tab phụ **Transcripts**.
   * Nhấn nút `➕ Import / Thêm transcript mới` để lưu trữ các văn bản ghi âm thô của bạn lên cơ sở dữ liệu.
2. **Cấu hình Skill Prompt:**
   * Sang tab phụ **Skill**.
   * Bạn có thể điều chỉnh cấu trúc bài viết, giọng văn (tone of voice) của y khoa tại đây. Prompt này sẽ được gửi tới LLM khi sinh bài.
3. **Sinh bài viết & Tự động Deploy:**
   * Tại tab phụ **Generate**, nhập **Target Keyword** (Từ khóa mục tiêu) và **File Slug**.
   * Chọn Transcript nguồn từ danh sách đã import.
   * Bật tùy chọn `Auto-deploy after generate` (Netlify token của bạn đã được cấu hình sẵn trong `secrets.toml`).
   * Nhấn **🚀 Run SEO Swarm**. 5 trang web HTML độc lập sẽ được tạo ra và tự động deploy song song lên Netlify. Bạn có thể theo dõi tiến trình trực quan tại tab phụ **Deploy**.

---

## 3. Khai thác tính năng Chat & Goal Mode của Hermes Agent
Giao diện **Agent HQ** và tab **Hermes** kết nối trực tiếp đến VPS của bạn thông qua `HERMES_API_URL`.

### 🚩 Định tuyến Model (Model Routing):
Hệ thống sử dụng chiến lược định tuyến model thông minh để tối ưu chi phí và hiệu năng:
* **gpt-5.5 (OpenAI Codex):** Dành cho các nhiệm vụ lập trình, cấu hình hệ thống phức tạp.
* **deepseek-4-flash (DeepSeek trực tiếp):** Dành cho tác vụ chat thường ngày, nghiên cứu tài liệu (Nhanh và Chi phí cực rẻ).
* **minimax-m3 (Minimax API):** Dành cho tác vụ sáng tạo, viết content y khoa (đã được cấu hình key của bạn).

### 🚩 Sử dụng Goal Mode (Chạy tác vụ nền dài hơi):
Nếu bạn có một tác vụ tốn thời gian (ví dụ: tạo hàng loạt kịch bản, phân tích dữ liệu lớn):
1. Vào tab **Hermes** -> chọn tab phụ **Goal Mode**.
2. Nhập tiêu đề và mô tả chi tiết yêu cầu của bạn, sau đó nhấn **✈ Launch goal**.
3. Hermes sẽ chạy ẩn dưới nền (chạy vòng lặp YOLO tối đa 50 lượt). Bạn có thể tắt máy tính đi ngủ, tiến trình và Console Thoughts Log Stream vẫn sẽ chạy độc lập trên VPS và lưu lại kết quả.

---

## 4. Xử lý hiển thị các Iframe bị chặn (Kanban, OpenClaw, Hermes Manage)
Các dịch vụ như Kanban Board (`workspace.tuandoctor.com`), OpenClaw Gateway (`gw-openclaw.tuandoctor.com`) và Hermes Dashboard (`dashboard.tuandoctor.com`) có chính sách bảo mật cookie khắt khe của trình duyệt (SameSite / Cross-Origin).

### 🚩 Giải pháp tối ưu:
* **Đăng nhập trước trên Tab mới:** Trước khi sử dụng các tab nhúng (Iframe) này trên app Streamlit, hãy nhấn nút **`⧉ Open in tab`** hoặc truy cập trực tiếp các địa chỉ trên ở một tab trình duyệt khác để đăng nhập tài khoản của bạn.
* Trình duyệt sẽ lưu Cookie dưới dạng First-party. Sau đó, khi quay lại ứng dụng Streamlit, giao diện Iframe nhúng sẽ tự động nhận diện phiên đăng nhập và hiển thị mượt mà không bị lỗi trắng trang.

---

## 5. Chạy local để đạt hiệu năng tốt nhất
Mặc dù bản Cloud (`agent-hermes-os.streamlit.app`) rất tiện lợi để xem trên điện thoại, việc chạy ứng dụng local trên máy tính cá nhân của bạn sẽ đem lại tốc độ phản hồi nhanh hơn và không lo bị ngắt kết nối WebSocket:
```powershell
streamlit run app.py --server.port 8530
```
Sau đó quét mã QR nội bộ hoặc truy cập `http://localhost:8530` để trải nghiệm mượt mà nhất.
