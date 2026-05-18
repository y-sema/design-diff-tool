# app.py（完成版）

```python
import os
import time
import asyncio
import traceback

from flask import Flask, render_template, request, redirect, url_for

from diff_tool import run_diff


app = Flask(__name__)


@app.route("/")
def index():
    """入力フォーム表示"""
    return render_template("form.html")


@app.route("/compare", methods=["POST"])
def compare():
    """フォーム送信後に差分比較を実行し、結果HTMLへリダイレクト"""

    try:
        # -----------------------------
        # フォーム値の取得
        # -----------------------------
        url_a = request.form["url_a"]
        url_b = request.form["url_b"]

        basic_id_a = request.form.get("basic_id_a", "")
        basic_pw_a = request.form.get("basic_pw_a", "")

        basic_id_b = request.form.get("basic_id_b", "")
        basic_pw_b = request.form.get("basic_pw_b", "")

        browser_width = int(request.form.get("browser_width", 1280))
        browser_height = int(request.form.get("browser_height", 800))

        diff_color_hex = request.form.get("diff_color", "#ff0000")

        # -----------------------------
        # 出力先ディレクトリ
        # -----------------------------
        timestamp = str(int(time.time()))
        output_dir = os.path.join("static", "results", timestamp)
        os.makedirs(output_dir, exist_ok=True)

        # -----------------------------
        # 差分比較実行
        # -----------------------------
        asyncio.run(
            run_diff(
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
            )
        )

        # -----------------------------
        # 結果HTMLへリダイレクト
        # -----------------------------
        return redirect(
            url_for(
                "static",
                filename=f"results/{timestamp}/design_diff_result.html",
            )
        )

    except Exception:
        # Render の Logs に詳細エラーを出力
        print("\n===== ERROR START =====")
        traceback.print_exc()
        print("===== ERROR END =====\n")

        return "Internal Server Error", 500


if __name__ == "__main__":
    app.run(debug=True)
```

---

## 保存後に実行するコマンド

```bash
git add app.py
git commit -m "Update app.py with detailed error logging"
git push
```

---

## 次の手順

1. Render が自動で再デプロイされる
2. フォームから比較実行
3. Render の Logs を確認
4. `===== ERROR START =====` 〜 `===== ERROR END =====` を確認

そのログを貼れば、原因を特定できます。
