import os
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("form.html")

@app.route("/compare", methods=["POST"])
def compare():
    url_a = request.form["url_a"]
    url_b = request.form["url_b"]
    basic_id_a = request.form.get("basic_id_a", "")
    basic_pw_a = request.form.get("basic_pw_a", "")
    basic_id_b = request.form.get("basic_id_b", "")
    basic_pw_b = request.form.get("basic_pw_b", "")
    width = int(request.form.get("width", 1280))
    diff_color = request.form.get("diff_color", "#ff0000")

    # Basic認証情報の埋め込み
    if basic_id_a and basic_pw_a:
        url_a = url_a.replace("://", f"://{basic_id_a}:{basic_pw_a}@")
    if basic_id_b and basic_pw_b:
        url_b = url_b.replace("://", f"://{basic_id_b}:{basic_pw_b}@")

    # 【修正ポイント】より高精度で即時レスポンスを返す無料APIに変更
    # WordPressより高速で、生成中エラーを起こしにくいエンドポイントです
    api_url_a = f"https://image.thumbalizr.com/api/v1/embed/free/a8cf0734bcdd1c4377bb4599f57ebbf7/?url={url_a}&width={width}"
    api_url_b = f"https://image.thumbalizr.com/api/v1/embed/free/a8cf0734bcdd1c4377bb4599f57ebbf7/?url={url_b}&width={width}"

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>デザイン差分結果</title>
<style>
body {{ background: #222; color: #fff; font-family: sans-serif; text-align: center; margin: 0; padding: 20px 0 170px 0; }}
.viewer {{ position: relative; display: inline-block; border: 2px solid #555; margin-top: 20px; line-height: 0; min-width: 300px; min-height: 300px; background: #333; }}
.base-image {{ display: block; max-width: 100%; height: auto; }}
.diff-layer-canvas {{ position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; opacity: 0.85; }}
.control-panel {{ position: fixed; left: 0; bottom: 0; width: 100%; box-sizing: border-box; padding: 15px 20px; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); border-top: 1px solid rgba(255,255,255,0.15); z-index: 9999; }}
.slider {{ width: min(800px, 80vw); }}
.value {{ margin-top: 8px; font-weight: bold; color: {diff_color}; }}
.color-picker {{ width: 50px; height: 32px; border: none; background: none; cursor: pointer; }}
#status {{ font-size: 18px; color: #ffc107; font-weight: bold; margin: 10px; }}
</style>
</head>
<body>
<h1>デザイン差分比較結果</h1>
<div id="status">🔄 外部APIからスクリーンショットを読み込み中...</div>

<div class="viewer">
    <img id="baseImg" class="base-image" crossorigin="anonymous">
    <canvas class="diff-layer-canvas" id="diffCanvas"></canvas>
</div>

<div class="control-panel">
    <input type="range" min="0" max="100" value="85" class="slider" id="slider">
    <div class="value" id="valueText">差分透明度：85%</div>
    <p>
        <label for="colorPicker">差分色：</label>
        <input type="color" id="colorPicker" class="color-picker" value="{diff_color}">
    </p>
</div>

<script>
const slider = document.getElementById('slider');
const valueText = document.getElementById('valueText');
const colorPicker = document.getElementById('colorPicker');
const canvas = document.getElementById('diffCanvas');
const ctx = canvas.getContext('2d');
const statusDiv = document.getElementById('status');
const baseImg = document.getElementById('baseImg');

const urlA = "{api_url_a}";
const urlB = "{api_url_b}";

let imgA = new Image();
let imgB = new Image();
imgA.crossOrigin = "Anonymous";
imgB.crossOrigin = "Anonymous";

let loadedCount = 0;

function checkImages() {{
    loadedCount++;
    if (loadedCount === 2) {{
        statusDiv.innerText = "🧠 差分を計算中...";
        setTimeout(processDiff, 300);
    }}
}}

imgA.src = urlA;
imgB.src = urlB;

imgA.onload = () => {{
    baseImg.src = imgA.src;
    checkImages();
}};
imgB.onload = checkImages;

imgA.onerror = imgB.onerror = () => {{
    statusDiv.innerHTML = "⚠️ スクショAPIの読み込みに失敗しました。<br>比較先URLが正しいか、またはローカルIP（localhost等）ではなく公開URL（https://...）を指定しているか確認してください。";
}};

function hexToRgb(hex) {{
    const bigint = parseInt(hex.slice(1), 16);
    return {{ r: (bigint >> 16) & 255, g: (bigint >> 8) & 255, b: bigint & 255 }};
}}

function processDiff() {{
    const width = Math.min(imgA.width, imgB.width);
    const height = Math.min(imgA.height, imgB.height);

    if(width <= 0 || height <= 0) {{
        statusDiv.innerText = "⚠️ 画像データの取得サイズが不正です。別のURLで試してください。";
        return;
    }}

    canvas.width = width;
    canvas.height = height;

    ctx.drawImage(imgA, 0, 0, width, height);
    const dataA = ctx.getImageData(0, 0, width, height).data;

    ctx.clearRect(0, 0, width, height);
    ctx.drawImage(imgB, 0, 0, width, height);
    const dataB = ctx.getImageData(0, 0, width, height).data;

    const resultImgData = ctx.createImageData(width, height);
    const resData = resultImgData.data;
    const targetColor = hexToRgb(colorPicker.value);

    for (let i = 0; i < dataA.length; i += 4) {{
        const rDiff = Math.abs(dataA[i] - dataB[i]);
        const gDiff = Math.abs(dataA[i+1] - dataB[i+1]);
        const bDiff = Math.abs(dataA[i+2] - dataB[i+2]);

        if (rDiff > 15 || gDiff > 15 || bDiff > 15) {{
            resData[i] = targetColor.r;
            resData[i+1] = targetColor.g;
            resData[i+2] = targetColor.b;
            resData[i+3] = 255;
        }} else {{
            resData[i+3] = 0;
        }}
    }}

    window.savedImgData = {{ dataA, dataB, width, height }};
    ctx.putImageData(resultImgData, 0, 0);
    statusDiv.innerText = "✅ 差分比較が完了しました！";
}}

function redrawDiff(hexColor) {{
    if (!window.savedImgData) return;
    const {{ dataA, dataB, width, height }} = window.savedImgData;
    const resultImgData = ctx.createImageData(width, height);
    const resData = resultImgData.data;
    const targetColor = hexToRgb(hexColor);

    for (let i = 0; i < dataA.length; i += 4) {{
        const rDiff = Math.abs(dataA[i] - dataB[i]);
        const gDiff = Math.abs(dataA[i+1] - dataB[i+1]);
        const bDiff = Math.abs(dataA[i+2] - dataB[i+2]);

        if (rDiff > 15 || gDiff > 15 || bDiff > 15) {{
            resData[i] = targetColor.r;
            resData[i+1] = targetColor.g;
            resData[i+2] = targetColor.b;
            resData[i+3] = 255;
        }} else {{
            resData[i+3] = 0;
        }}
    }}
    ctx.putImageData(resultImgData, 0, 0);
}}

canvas.style.opacity = slider.value / 100;
slider.addEventListener('input', () => {{
    canvas.style.opacity = slider.value / 100;
    valueText.textContent = '差分透明度：' + slider.value + '%';
}});

colorPicker.addEventListener('input', () => {{
    redrawDiff(colorPicker.value);
    valueText.style.color = colorPicker.value;
}});
</script>
</body>
</html>
"""