#!/usr/bin/env python3
"""Entry program for make.fun bounty news-image-20261119.

Standard library only: copies the pre-drawn front page (entry.png, drawn by
draw.py) to the output directory as entry.png.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(os.path.join(HERE, "entry.png"),
                    os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
