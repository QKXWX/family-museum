# -*- coding: utf-8 -*-
"""生成一组演示用的抽象「照片卡」，不是真实照片。

用于跑通扫描、去重、时间轴和博物馆页面；换成你自己的照片目录即可。
"""

import datetime
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent / "demo-photos"
FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
ITEMS = [
    ("2017/春节/年夜饭.jpg", (2017, 1, 28, 18, 30), "2017 春节 · 家里的灯"),
    ("2017/夏/第一次看海.jpg", (2017, 7, 16, 11, 20), "2017 夏 · 第一次看海"),
    ("2018/秋/开学那天.jpg", (2018, 9, 1, 7, 40), "2018 秋 · 开学那天"),
    ("2019/春/老屋.jpg", (2019, 4, 5, 16, 10), "2019 春 · 老屋的院子"),
    ("2019/夏/海边.jpg", (2019, 7, 20, 19, 10), "2019 夏 · 海边落日"),
    ("2020/冬/窗花.jpg", (2020, 1, 24, 9, 0), "2020 冬 · 窗上的霜"),
    ("2021/夏/搬家.jpg", (2021, 6, 12, 14, 30), "2021 夏 · 搬家那天"),
    ("2022/秋/山里.jpg", (2022, 10, 3, 10, 0), "2022 秋 · 山里的雾"),
    ("2023/春/第一场雨.jpg", (2023, 4, 18, 17, 20), "2023 春 · 第一场雨"),
    ("2025/冬/雪.jpg", (2025, 1, 6, 8, 10), "2025 冬 · 早上的雪"),
]


def gradient(width, height, top, bottom):
    rows = np.linspace(0, 1, height)[:, None]
    channels = []
    for index in range(3):
        channels.append((top[index] * (1 - rows) + bottom[index] * rows).astype(np.uint8))
    arr = np.stack(channels, axis=2)
    return Image.fromarray(np.repeat(arr, width, axis=1), "RGB")


def make_photo(path, date, caption):
    width, height = 1200, 800
    palettes = [((28, 39, 54), (184, 118, 82)), ((48, 57, 46), (205, 174, 120)),
                ((39, 34, 55), (136, 108, 126)), ((22, 43, 53), (105, 150, 158))]
    top, bottom = palettes[(date.year + date.month) % len(palettes)]
    image = gradient(width, height, top, bottom)
    draw = ImageDraw.Draw(image, "RGBA")
    draw.ellipse((760, 80, 1160, 480), fill=(255, 236, 203, 34))
    draw.rectangle((0, 620, width, 800), fill=(10, 12, 16, 90))
    draw.line((80, 650, 1120, 650), fill=(255, 255, 255, 38), width=2)
    font = ImageFont.truetype(FONT, 54)
    small = ImageFont.truetype(FONT, 24)
    draw.text((80, 690), caption, font=font, fill=(247, 239, 226))
    draw.text((82, 752), "FAMILY MUSEUM · DEMO CARD", font=small, fill=(210, 195, 177, 180))
    exif = Image.Exif()
    exif[36867] = date.strftime("%Y:%m:%d %H:%M:%S")
    exif[306] = date.strftime("%Y:%m:%d %H:%M:%S")
    exif[270] = caption
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "JPEG", quality=88, exif=exif)


def main():
    if ROOT.exists():
        shutil.rmtree(ROOT)
    for rel, fields, caption in ITEMS:
        date = datetime.datetime(*fields)
        make_photo(ROOT / rel, date, caption)
    # 故意做一张完全重复的，展示去重统计
    duplicate = ROOT / "2019/夏/海边-副本.jpg"
    shutil.copy2(ROOT / "2019/夏/海边.jpg", duplicate)
    print("demo photos:", ROOT)


if __name__ == "__main__":
    main()
