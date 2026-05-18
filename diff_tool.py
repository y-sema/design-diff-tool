import os
import base64
from PIL import Image, ImageChops
from playwright.async_api import async_playwright


async def scroll_to_bottom_and_back(page):
    """ページ最下部までスクロールしてアニメーションを発火させた後、先頭に戻る"""

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


async def create_context(browser, basic_id, basic_pw):
    """Basic認証付きのブラウザコンテキストを作成"""

    context_args = {}

    if basic_id and basic_pw:
        context_args["http_credentials"] = {
            "username": basic_id,
            "password": basic_pw,
        }

    return await browser.new_context(**context_args)


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
    """指定URLのフルページスクリーンショットを取得"""

    print(f"🔄 {label} の処理を開始...")

    context = await create_context(browser, basic_id, basic_pw)
    page = await context.new_page()

    await page.set_viewport_size(
        {
            "width": browser_width,
            "height": browser_height,
        }
    )

    try:
        await page.goto(url, wait_until="networkidle", timeout=120000)
        await scroll_to_bottom_and_back(page)
        await page.screenshot(path=save_path, full_page=True)
        print(f"✅ {label} の撮影完了")

    finally:
        await context.close()


def create_diff_image(img_a_path, img_b_path, diff_path):
    """2枚の画像から差分マスク画像を生成"""

    print("🧠 差分画像を生成中...")

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

    print("✅ 差分画像の生成完了")


def create_result_html(html_path, diff_path, diff_color_hex):
    """差分確認用HTMLを生成"""

    with open(diff_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

    diff_base64_url = f"data:image/png;base64,{encoded_string}"

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>デザイン差分結果</title>
<style>
body {{
    background: #222;
    color: #fff;
    font-family: sans-serif;
    text-align: center;
    margin: 0;
    padding: 20px;
    padding-bottom: 170px;
}}

h1 {{
    margin-bottom: 10px;
}}

p {{
    color: #ccc;
}}

.viewer {{
    position: relative;
    display: inline-block;
    border: 2px solid #555;
    margin-top: 20px;
    line-height: 0;
}}

.base-image {{
    display: block;
    max-width: 100%;
}}

.diff-layer-canvas {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    opacity: 0.85;
}}

.control-panel {{
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    box-sizing: border-box;
    padding: 15px 20px;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border-top: 1px solid rgba(255, 255, 255, 0.15);
    z-index: 9999;
}}

.slider {{
    width: min(800px, 80vw);
}}

.value {{
    margin-top: 8px;
    font-weight: bold;
    color: {diff_color_hex};
}}

.color-picker {{
    width: 50px;
    height: 32px;
    border: none;
    background: none;
    padding: 0;
    cursor: pointer;
}}
</style>
</head>
<body>

<h1>デザイン差分比較結果</h1>

<p>
スライダーで差分の濃さを調整できます。<br>
カラーピッカーで差分色を変更できます。
</p>

<div class="viewer">
    <img src="screenshot_A.png" class="base-image">
    <canvas class="diff-layer-canvas" id="diffCanvas"></canvas>
</div>

<div class="control-panel">
    <input
        type="range"
        min="0"
        max="100"
        value="85"
        class="slider"
        id="slider"
    >

    <div class="value" id="valueText">
        差分透明度：85%
    </div>

    <p>
        <label for="colorPicker">差分色：</label>
        <input
            type="color"
            id="colorPicker"
            class="color-picker"
            value="{diff_color_hex}"
        >
    </p>
</div>

<script>
const slider = document.getElementById('slider');
const valueText = document.getElementById('valueText');
const colorPicker = document.getElementById('colorPicker');
const canvas = document.getElementById('diffCanvas');
const ctx = canvas.getContext('2d');

const maskImg = new Image();
maskImg.src = '{diff_base64_url}';

maskImg.onload = () => {{
    canvas.width = maskImg.width;
    canvas.height = maskImg.height;
    drawDiff(colorPicker.value);
}};

function hexToRgb(hex) {{
    const bigint = parseInt(hex.slice(1), 16);
    return {{
        r: (bigint >> 16) & 255,
        g: (bigint >> 8) & 255,
        b: bigint & 255
    }};
}}

function drawDiff(hexColor) {{
    if (!canvas.width || !canvas.height) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(maskImg, 0, 0);

    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imgData.data;
    const targetColor = hexToRgb(hexColor);

    for (let i = 0; i < data.length; i += 4) {{
        if (data[i] > 10 && data[i + 1] > 10 && data[i + 2] > 10) {{
            data[i] = targetColor.r;
            data[i + 1] = targetColor.g;
            data[i + 2] = targetColor.b;
        }}
    }}

    ctx.putImageData(imgData, 0, 0);
}}

canvas.style.opacity = slider.value / 100;

slider.addEventListener('input', () => {{
    canvas.style.opacity = slider.value / 100;
    valueText.textContent = '差分透明度：' + slider.value + '%';
}});

colorPicker.addEventListener('input', () => {{
    drawDiff(colorPicker.value);
    valueText.style.color = colorPicker.value;
}});
</script>

</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


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
    """差分比較のメイン処理"""

    os.makedirs(output_dir, exist_ok=True)

    img_a_path = os.path.join(output_dir, "screenshot_A.png")
    img_b_path = os.path.join(output_dir, "screenshot_B.png")
    diff_path = os.path.join(output_dir, "diff_result.png")
    html_path = os.path.join(output_dir, "design_diff_result.html")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        await capture_page(
            browser,
            url_a,
            basic_id_a,
            basic_pw_a,
            img_a_path,
            "URL_A",
            browser_width,
            browser_height,
        )

        await capture_page(
            browser,
            url_b,
            basic_id_b,
            basic_pw_b,
            img_b_path,
            "URL_B",
            browser_width,
            browser_height,
        )

        await browser.close()

    create_diff_image(img_a_path, img_b_path, diff_path)
    create_result_html(html_path, diff_path, diff_color_hex)

    return html_path

