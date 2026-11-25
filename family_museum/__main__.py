# -*- coding: utf-8 -*-
"""命令行入口：family-museum build ~/Photos --out museum"""

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from .build import scan, write_site


def main(argv=None):
    parser = argparse.ArgumentParser(prog="family-museum", description="把照片整理成家庭数字博物馆")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="扫描照片并生成静态博物馆")
    build.add_argument("photos", help="照片目录")
    build.add_argument("--out", default="museum", help="输出目录，默认 ./museum")
    build.add_argument("--title", default="家展", help="博物馆标题")
    build.add_argument("--copy", action="store_true", help="把原图复制进博物馆（默认只生成缩略图）")
    build.add_argument("--limit", type=int, default=None, help="最多处理多少张（调试用）")
    build.add_argument("--json", action="store_true", help="打印 JSON 摘要")
    build.add_argument("--open", action="store_true", help="生成后打开浏览器")
    args = parser.parse_args(argv)

    if args.command == "build":
        if not Path(args.photos).is_dir():
            print("照片目录不存在：%s" % args.photos, file=sys.stderr)
            return 2

        def progress(index, total, name):
            if total >= 20:
                print("\r扫描 %d/%d %s" % (index, total, name[:40]), end="", flush=True)

        data = scan(args.photos, args.out, copy_originals=args.copy, limit=args.limit, progress=progress)
        if data["stats"]["photos"] == 0:
            print("\n没有找到可读的照片。支持 jpg/png/webp/tif/bmp。", file=sys.stderr)
            return 1
        page = write_site(data, args.out, args.title)
        print("\n博物馆：%s" % page)
        print("照片 %d 张 / 重复 %d 张 / 年份 %s / 地点 %d 个" % (
            data["stats"]["photos"], data["stats"]["duplicates"],
            data["stats"]["year_span"], data["stats"]["places"]))
        if args.json:
            print(json.dumps({"stats": data["stats"], "exhibitions": data["exhibitions"]},
                             ensure_ascii=False, indent=2))
        if args.open:
            webbrowser.open(page.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
