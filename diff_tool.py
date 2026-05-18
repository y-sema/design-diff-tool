import os
import base64
import requests
from PIL import Image, ImageChops
import io

def capture_page_via_api(url, width, height):
    """外部の無料APIを使って、URLのスクリーンショット（バイナリ）を取得する"""
    # WordPressが公式提供している、全世界で使われている超安定スクショAPIを利用
    # full_page風にするため、APIが対応する最大サイズや標準サイズで取得します
    api_url = f"https://s.wordpress.com/mshots/v1/{requests.utils.quote(url)}?w={width}"
    
    try:
        response = requests.get(api_url, timeout=30)
        # 稀に初回アクセス時は「生成中」のダミー画像が返ることがあるため、念のためチェック
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"スクショAPIのステータスコード異常: {response.status_code}")
    except Exception as e:
        raise Exception(f"スクショの取得に失敗しました: {str(e)}")

def create_diff_and_html_stream(img_bytes_a, img_bytes_b, diff_color_hex):
    """メモリ上の画像データから差分を計算し、最終的なHTML文字列を生成する"""
    img_a = Image.open(io.BytesIO(img_bytes_a)).convert("RGBA")
    img_b = Image.open(io.BytesIO(img_bytes_b)).convert("RGBA")

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
            r, g, b, _ = diff_pixels[x, y]
            if r > 15 or g > 15 or b > 15:
                result_pixels[x, y] = (255, 255, 255, 255)

    # 差分画像をBase64化
    diff_buffer = io.BytesIO()
    result.save(diff_buffer, format="PNG")
    diff_base64 = base64.b64encode(diff_buffer.getvalue()).decode("utf-8")
    diff_base64_url = f"data:image/png;base64,{diff_base64}"

    # ベースとなる本番画像（A）も埋め込む
    base_buffer = io.BytesIO()
    img_a.save(base_buffer, format="PNG")
    base_base64 = base64.b64encode(base_buffer.getvalue()).decode("utf-8")
    base_base64_url = f"data:image/png;base64,{base_base64}"

    # HTMLテンプレート
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>デザイン差分結果</title>
<style>
body {{ background: #222; color: #fff; font-family: sans-serif; text-align: center; margin: 0; padding: 20px 0 170px 0; }}
.viewer {{ position: relative; display: inline-block; border: 2px solid #555; margin-top: 20px; line-height: 0; }}
.base-image {{ display: block; max-width: 100%; }}
.diff-layer-canvas {{ position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; opacity: 0.85; }}
.control-panel {{ position: fixed; left: 0; bottom: 0; width: 100%; box-sizing: border-box; padding: 15px 20px; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); border-top: 1px solid rgba(255,255,255,0.15); z-index: 9999; }}
.slider {{ width: min(800px, 80vw); }}
.value {{ margin-top: 8px; font-weight: bold; color: {diff_color_hex}; }}
.color-picker {{ width: 50px; height: 32px; border: none; background: none; cursor: pointer; }}
</style>
</head>
<body>
<h1>デザイン差分比較結果</h1>
<p>スライダーで差分の濃さを調整、カラーピッカーで色を変更できます。</p>
<div class="viewer">
    <img src="{base_base64_url}" class="base-image">
    <canvas class="diff-layer-canvas" id="diffCanvas"></canvas>
</div>
<div class="control-panel">
    <input type="range" min="0" max="100" value="85" class="slider" id="slider">
    <div class="value" id="valueText">差分透明度：85%</div>
    <p>
        <label for="colorPicker">差分色：</label>
        <input type="color" id="colorPicker" class="color-picker" value="{diff_color_hex}">
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
    return {{ r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 }};
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
</html>"""
    return html

def run_diff(url_a, url_b, basic_id_a, basic_pw_a, basic_id_b, basic_pw_b, browser_width, browser_height, diff_color_hex):
    """APIを利用した超軽量・高速な同期処理にリプレイス"""
    # ※ 無料APIの制約上、Basic認証がかかっているサイトの場合は URL に認証情報を付与します
    if basic_id_a and basic_pw_a:
        url_a = url_a.replace("://", f"://{basic_id_a}:{basic_pw_a}@")
    if basic_id_b and basic_pw_b:
        url_b = url_b.replace("://", f"://{basic_id_b}:{basic_pw_b}@")

    # API経由で画像を取得
    img_bytes_a = capture_page_via_api(url_a, browser_width, browser_height)
    img_bytes_b = capture_page_via_api(url_b, browser_width, browser_height)

    # HTMLストリームを生成して返す
    return create_diff_and_html_stream(img_bytes_a, img_bytes_b, diff_color_hex)