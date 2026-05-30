from playwright.sync_api import sync_playwright

BASE = "http://localhost:8530"
shots = [
    ("memory",   f"{BASE}/?nav=memory",   "shot_memory.png",   "Obsidian Vault"),
    ("openclaw", f"{BASE}/?nav=openclaw", "shot_openclaw.png", "OpenClaw"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    for name, url, out, needle in shots:
        page.goto(url, wait_until="networkidle", timeout=60000)
        # chờ Streamlit render xong text đặc trưng
        try:
            page.get_by_text(needle, exact=False).first.wait_for(timeout=30000)
        except Exception:
            pass
        page.wait_for_timeout(2500)
        page.screenshot(path=out, full_page=True)
        print(f"{name}: saved {out}")
    browser.close()
