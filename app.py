from flask import Flask, render_template, request, redirect
import uuid
import os
import asyncio
from diff_tool import run_diff

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "static", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("form.html")


@app.route("/compare", methods=["POST"])
def compare():
    # フォーム値取得
    url_a = request.form.get("url_a", "")
    url_b = request.form.get("url_b", "")

    basic_id_a = request.form.get("basic_id_a", "")
    basic_pw_a = request.form.get("basic_pw_a", "")

    basic_id_b = request.form.get("basic_id_b", "")
    basic_pw_b = request.form.get("basic_pw_b", "")

    diff_color = request.form.get("diff_color", "#ff0000")

    width = int(request.form.get("width", 1280))
    height = int(request.form.get("height", 800))

    # 一意の結果フォルダ
    result_id = str(uuid.uuid4())
    output_dir = os.path.join(RESULTS_DIR, result_id)
    os.makedirs(output_dir, exist_ok=True)

    # 非同期処理実行
    asyncio.run(
        run_diff(
            url_a=url_a,
            url_b=url_b,
            basic_id_a=basic_id_a,
            basic_pw_a=basic_pw_a,
            basic_id_b=basic_id_b,
            basic_pw_b=basic_pw_b,
            browser_width=width,
            browser_height=height,
            diff_color_hex=diff_color,
            output_dir=output_dir,
        )
    )

    # 結果ページへリダイレクト
    return redirect(f"/static/results/{result_id}/design_diff_result.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)