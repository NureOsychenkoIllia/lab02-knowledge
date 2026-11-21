"""Render terminal-style PNG screenshots from command output."""

import argparse
import subprocess
import textwrap

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/TTF/DejaVuSansMono.ttf"
SIZE = 15
PAD = 16
BG = (30, 30, 46)
FG = (205, 214, 244)
PROMPT = (166, 227, 161)

font = ImageFont.truetype(FONT_PATH, SIZE)


def run(command):
    proc = subprocess.run(
        command, shell=True, capture_output=True, text=True, executable="/bin/bash"
    )
    return proc.stdout.rstrip("\n").split("\n")


def render(command, lines, out, width_chars=100):
    wrapped = []
    for line in lines:
        wrapped += textwrap.wrap(line, width_chars, replace_whitespace=False,
                                 drop_whitespace=True) or [""]
    body = ["$ " + command] + wrapped
    lh = int(SIZE * 1.45)
    width = int(max(font.getlength(s) for s in body) + 2 * PAD)
    height = PAD + lh * len(body) + PAD

    img = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(img)

    y = PAD
    for i, line in enumerate(body):
        color = PROMPT if i == 0 and line.startswith("$ ") else FG
        d.text((PAD, y), line, font=font, fill=color)
        y += lh
    img.save(out)
    print(f"written {out}  ({width}x{height})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="shell command to execute")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lines", default=None, help="a:b (1-indexed, inclusive)")
    ap.add_argument("--width", type=int, default=100, help="wrap column")
    args = ap.parse_args()

    lines = run(args.run)
    if args.lines:
        a, b = (int(x) if x else None for x in args.lines.split(":"))
        lines = lines[(a or 1) - 1 : b]
    render(args.run, lines, args.out, args.width)


if __name__ == "__main__":
    main()
