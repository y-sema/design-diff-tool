import os
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