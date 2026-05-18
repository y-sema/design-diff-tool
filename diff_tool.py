import os
import base64
from PIL import Image, ImageChops
from playwright.async_api import async_playwright


# ==============================
# スクロール処理
# ==============================
async def scroll_to_bottom_and_back(page):
    """ページを最後までスクロールしてアニメーション発火→トップへ戻す"""

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


# ==============================
# context生成（Basic認証対応）
# ==============================
async def create_context(browser, basic_id, basic_pw):
    context_args = {}

    if basic_id and basic_pw:
        context_args["http_credentials"] = {
            "username": basic_id,
            "password": basic_pw,
        }

    return await browser.new_context(**context_args)


# ==============================
# スクリーンショット取得
# ==============================
async def capture_page(
    browser,
    url,
    basic_id,
    basic_pw,
    save_path,
    label,
    browser_width,
    browser_height,
):
    print(f"🔄 {label} 撮影開始...")

    context = await create_context(browser, basic_id, basic_pw)
    page = await context.new_page()

    await page.set_viewport_size({
        "width": browser_width,
        "height": browser_height,
    })

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=120000)
        await scroll_to_bottom_and_back(page)
        await page.screenshot(path=save_path, full_page=True)

        print(f"✅ {label} 撮影完了")

    finally:
        await context.close()


# ==============================
# 差分画像生成
# ==============================
def create_diff_image(img_a_path, img_b_path, diff_path):
    print("🧠 差分画像生成中...")

    img_a = Image.open(img_a_path).convert("RGBA")
    img_b = Image.open(img_b_path).convert("RGBA")

    width = min(img_a.width, img_b.width)
    height = min(img_a.height, img_b.height)

    img_a = img_a.crop((0, 0, width, height))
    img_b = img_b.crop((0, 0, width, height))

    diff = ImageChops.difference(img_a, img_b)

    result = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    diff_pixels = diff.load()
    result_pixels = result.load()

    for y in range(height):
        for x in range(width):
            r, g, b, a = diff_pixels[x, y]

            if r > 10 or g > 10 or b > 10:
                result_pixels[x, y] = (255, 255, 255, 255)

    result.save(diff_path)

    print("✅ 差分画像生成完了")


# ==============================
# HTML生成（差分ビューア）
# ==============================
def create_result_html(html_path, diff_path, diff_color_hex):
    with open(diff_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    diff_base64_url = f"data:image/png;base64,{encoded}"

    html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Design Diff Result</title>

<style>
body {{
    background:#222;
    color:#fff;
    font-family:sans-serif;
    text-align:center;
    margin:0;
    padding:20px;
}}

.viewer {{
    position:relative;
    display:inline-block;
    border:2px solid #555;
}}

.base {{
    display:block;
    max-width:100%;
}}

canvas {{
    position:absolute;
    inset:0;
    width:100%;
    height:100%;
    pointer-events:none;
    opacity:0.85;
}}

.control {{
    position:fixed;
    bottom:0;
    left:0;
    width:100%;
    background:rgba(0,0,0,0.85);
    padding:15px;
}}

.value {{
    color:{diff_color_hex};
    margin-top:8px;
}}
</style>
</head>

<body>

<h1>デザイン差分結果</h1>

<div class="viewer">
    <img src="screenshot_A.png" class="base">
    <canvas id="canvas"></canvas>
</div>

<div class="control">
    <input type="range" id="slider" min="0" max="100" value="85">
    <div id="value" class="value">85%</div>

    <input type="color" id="color" value="{diff_color_hex}">
</div>

<script>
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

const img = new Image();
img.src = "{diff_base64_url}";

const slider = document.getElementById("slider");
const value = document.getElementById("value");
const color = document.getElementById("color");

img.onload = () => {{
    canvas.width = img.width;
    canvas.height = img.height;
    draw(color.value);
}};

function hexToRgb(hex) {{
    const n = parseInt(hex.slice(1), 16);
    return {{
        r:(n>>16)&255,
        g:(n>>8)&255,
        b:n&255
    }};
}}

function draw(hex) {{
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.drawImage(img,0,0);

    const d = ctx.getImageData(0,0,canvas.width,canvas.height);
    const data = d.data;
    const c = hexToRgb(hex);

    for(let i=0;i<data.length;i+=4){{
        if(data[i]>10 && data[i+1]>10 && data[i+2]>10){{
            data[i]=c.r;
            data[i+1]=c.g;
            data[i+2]=c.b;
        }}
    }}

    ctx.putImageData(d,0,0);
}}

slider.oninput = () => {{
    canvas.style.opacity = slider.value/100;
    value.innerText = slider.value + "%";
}};

color.oninput = () => draw(color.value);
</script>

</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


# ==============================
# メイン処理（←ここが重要）
# ==============================
async def run_diff(
    url_a,
    url_b,
    basic_id_a,
    basic_pw_a,
    basic_id_b,
    basic_pw_b,
    browser_width,
    browser_height,
    diff_color_hex,
    output_dir,
):
    os.makedirs(output_dir, exist_ok=True)

    img_a = os.path.join(output_dir, "screenshot_A.png")
    img_b = os.path.join(output_dir, "screenshot_B.png")
    diff = os.path.join(output_dir, "diff.png")
    html = os.path.join(output_dir, "design_diff_result.html")

    async with async_playwright() as p:

        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        await capture_page(
            browser, url_a, basic_id_a, basic_pw_a,
            img_a, "URL_A", browser_width, browser_height
        )

        await capture_page(
            browser, url_b, basic_id_b, basic_pw_b,
            img_b, "URL_B", browser_width, browser_height
        )

        await browser.close()

    create_diff_image(img_a, img_b, diff)
    create_result_html(html, diff, diff_color_hex)

    return html