import os
import base64
from PIL import Image, ImageChops
from playwright.async_api import async_playwright


# =========================
# スクロール処理
# =========================
async def scroll_to_bottom_and_back(page):
    total_height = await page.evaluate("document.body.scrollHeight")
    current_position = 0
    scroll_step = 400

    while current_position < total_height:
        current_position += scroll_step
        await page.evaluate(f"window.scrollTo(0, {current_position})")
        await page.wait_for_timeout(150)
        total_height = await page.evaluate("document.body.scrollHeight")

    await page.wait_for_timeout(2000)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)


# =========================
# Context作成
# =========================
async def create_context(browser, basic_id, basic_pw):
    context_args = {}

    if basic_id and basic_pw:
        context_args["http_credentials"] = {
            "username": basic_id,
            "password": basic_pw,
        }

    return await browser.new_context(**context_args)


# =========================
# スクショ取得
# =========================
async def capture_page(browser, url, basic_id, basic_pw, save_path, label, w, h):
    context = await create_context(browser, basic_id, basic_pw)
    page = await context.new_page()

    await page.set_viewport_size({"width": w, "height": h})

    try:
        await page.goto(url, wait_until="networkidle", timeout=120000)
        await scroll_to_bottom_and_back(page)
        await page.screenshot(path=save_path, full_page=True)
    finally:
        await context.close()


# =========================
# 差分生成
# =========================
def create_diff_image(img_a_path, img_b_path, diff_path):
    img_a = Image.open(img_a_path).convert("RGBA")
    img_b = Image.open(img_b_path).convert("RGBA")

    width = min(img_a.width, img_b.width)
    height = min(img_a.height, img_b.height)

    img_a = img_a.crop((0, 0, width, height))
    img_b = img_b.crop((0, 0, width, height))

    diff = ImageChops.difference(img_a, img_b)

    result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = diff.load()
    r = result.load()

    for y in range(height):
        for x in range(width):
            rr, gg, bb, aa = d[x, y]
            if rr > 10 or gg > 10 or bb > 10:
                r[x, y] = (255, 255, 255, 255)

    result.save(diff_path)


# =========================
# HTML生成
# =========================
def create_result_html(html_path, diff_path, diff_color_hex):
    with open(diff_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    diff_url = f"data:image/png;base64,{b64}"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Diff</title>
<style>
body {{ background:#222; color:#fff; text-align:center; }}
.viewer {{ position:relative; display:inline-block; }}
canvas {{ position:absolute; top:0; left:0; }}
</style>
</head>
<body>

<h1>差分結果</h1>

<div class="viewer">
    <img src="screenshot_A.png">
    <canvas id="c"></canvas>
</div>

<input type="range" id="s" min="0" max="100" value="80">

<script>
const img = new Image();
img.src = "{diff_url}";

const canvas = document.getElementById("c");
const ctx = canvas.getContext("2d");

img.onload = () => {{
    canvas.width = img.width;
    canvas.height = img.height;
    ctx.drawImage(img, 0, 0);
}};
</script>

</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


# =========================
# メイン処理
# =========================
async def run_diff(url_a, url_b, id_a, pw_a, id_b, pw_b, w, h, color, outdir):

    os.makedirs(outdir, exist_ok=True)

    a = os.path.join(outdir, "a.png")
    b = os.path.join(outdir, "b.png")
    d = os.path.join(outdir, "diff.png")
    html = os.path.join(outdir, "result.html")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        await capture_page(browser, url_a, id_a, pw_a, a, "A", w, h)
        await capture_page(browser, url_b, id_b, pw_b, b, "B", w, h)

        await browser.close()

    create_diff_image(a, b, d)
    create_result_html(html, d, color)

    return html