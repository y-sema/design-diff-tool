import os
import asyncio
import threading
from flask import Flask, render_template, request, redirect, url_for
from diff_tool import run_diff

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "results")

# 処理中かどうかを管理する簡易フラグ
is_processing = False

@app.route("/")
def index():
    return render_template("form.html")

def start_async_task(loop, coro):
    """別スレッドで安全に非同期処理を実行する"""
    asyncio.set_event_loop(loop)
    loop.run_until_complete(coro)

@app.route("/compare", methods=["POST"])
def compare():
    global is_processing
    if is_processing:
        return "現在、別の比較処理が実行中です。しばらくお待ちください。", 429

    url_a = request.form["url_a"]
    url_b = request.form["url_b"]
    basic_id_a = request.form.get("basic_id_a", "")
    basic_pw_a = request.form.get("basic_pw_a", "")
    basic_id_b = request.form.get("basic_id_b", "")
    basic_pw_b = request.form.get("basic_pw_b", "")
    width = int(request.form.get("width", 1280))
    height = int(request.form.get("height", 800))
    diff_color = request.form.get("diff_color", "#ff0000")

    is_processing = True

    try:
        # 新しいイベントループを作成して、別スレッドでPlaywrightを実行（Flaskのタイムアウト回避）
        new_loop = asyncio.new_event_loop()
        coro = run_diff(
            url_a=url_a,
            url_b=url_b,
            basic_id_a=basic_id_a,
            basic_pw_a=basic_pw_a,
            basic_id_b=basic_id_b,
            basic_pw_b=basic_pw_b,
            browser_width=width,
            browser_height=height,
            diff_color_hex=diff_color,
            output_dir=OUTPUT_DIR,
        )
        
        t = threading.Thread(target=start_async_task, args=(new_loop, coro))
        t.start()
        t.join() # 処理が終わるまで待つ
        
    except Exception as e:
        is_processing = False
        return f"エラーが発生しました: {str(e)}", 500

    is_processing = False

    # 絶対パスではなくFlaskの静的ファイルURLにリダイレクト、またはHTMLを返す
    return """
    <h2>比較が完了しました</h2>
    <p><a href="/static/results/design_diff_result.html" target="_blank" style="font-size:18px; font-weight:bold; color:#007bff;">👉 結果を表示する</a></p>
    <p><a href="/">トップに戻る</a></p>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))