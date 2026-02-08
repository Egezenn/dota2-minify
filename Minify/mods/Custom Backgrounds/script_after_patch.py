import os
import sys
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)


def main():
    # aye, clever!
    if os.path.exists(p := os.path.join(current_dir, "video_success")):
        with open(os.path.join(current_dir, "styling.css")) as f:
            data = f.read()

        data = re.sub(r"(\s*)/\* (background-image: .*?); \*/(\s*/\* replace \*/)", r"\1\2;\3", data)

        with open(os.path.join(current_dir, "styling.css"), "w") as f:
            f.write(data)
        os.remove(p)
