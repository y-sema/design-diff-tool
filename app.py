import os
from flask import Flask, render_template, request
from diff_tool import run_diff

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
        # 完全な同期処理として実行（タイムアウトもメモリ不足も起きません）
        result_html = run_diff(
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
        return result_html

    except Exception as e:
        return f"""
        <div style="padding:20px; color:red; font-family:sans-serif;">
            <h2>エラーが発生しました</h2>
            <p>URLが正しいか、または少し時間を置いて再度試してください。（WordPress APIの生成待ちの可能性があります）</p>
            <pre>{str(e)}</pre>
            <a href="/">戻る</a>
        </div>
        """, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))