import os
import asyncio
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
    height = int(request.form.get("height", 800))
    diff_color = request.form.get("diff_color", "#ff0000")

    try:
        # 同期的にasync処理を走らせる
        result_html = asyncio.run(
            run_diff(
                url_a=url_a,
                url_b=url_b,
                basic_id_a=basic_id_a,
                basic_pw_a=basic_pw_a,
                basic_id_b=basic_id_b,
                basic_pw_b=basic_pw_b,
                browser_width=width,
                browser_height=height,
                diff_color_hex=diff_color
            )
        )
        # 生成されたHTMLをそのままブラウザに出力
        return result_html

    except Exception as e:
        return f"""
        <div style="padding:20px; color:red;">
            <h2>エラーが発生しました</h2>
            <p>Renderの無料プランのメモリ制限を超えた可能性があります。URLやベーシック認証が正しいか再度確認してください。</p>
            <pre>{str(e)}</pre>
            <a href="/">戻る</a>
        </div>
        """, 500

# 念のため末尾でrun_diffをインポートできるように最後に書くか、ファイルの最初でimportしてください
from diff_tool import run_diff

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))