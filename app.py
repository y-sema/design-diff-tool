import os
import uuid
import asyncio
from flask import Flask, render_template, request, send_from_directory

from diff_tool import run_diff

app = Flask(__name__)

OUTPUT_DIR = os.path.join("static", "results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("form.html")


@app.route("/compare", methods=["POST"])
def compare():
    url_a = request.form.get("url_a")
    url_b = request.form.get("url_b")

    basic_id_a = request.form.get("basic_id_a", "")
    basic_pw_a = request.form.get("basic_pw_a", "")
    basic_id_b = request.form.get("basic_id_b", "")
    basic_pw_b = request.form.get("basic_pw_b", "")

    diff_color = request.form.get("diff_color", "#ff0000")
    width = int(request.form.get("width", 1280))
    height = int(request.form.get("height", 800))

    # ユニークフォルダ（Render対応）
    job_id = str(uuid.uuid4())
    output_dir = os.path.join(OUTPUT_DIR, job_id)

    html_path = asyncio.run(
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

    # HTMLは static 配下なのでそのまま返せる
    return send_from_directory(
        output_dir,
        "design_diff_result.html"
    )


if __name__ == "__main__":
    app.run(debug=True)