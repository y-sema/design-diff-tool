from flask import Flask, render_template, request, send_file
import asyncio
import os
from diff_tool import run_diff

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "results")


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

    os.makedirs(OUTPUT_DIR, exist_ok=True)

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
            output_dir=OUTPUT_DIR,
        )
    )

    return send_file(html_path)


if __name__ == "__main__":
    app.run(debug=True)