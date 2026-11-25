# -*- coding: utf-8 -*-
"""把一 folders 照片整理成一座可离线打开的「家庭数字博物馆」。

只读原图；生成缩略图、data.js 和静态页面。不上传任何东西。
"""

import datetime
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageOps

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_exif_date(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d"):
        try:
            return datetime.datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def _to_degrees(values):
    try:
        deg, minute, second = [float(item) for item in values]
    except (TypeError, ValueError):
        return None
    return deg + minute / 60.0 + second / 3600.0


def read_metadata(path):
    """返回 (拍摄时间, 描述, GPS)。读不到就用文件时间。"""
    captured = None
    description = ""
    gps = None
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            ifd = {}
            try:
                ifd = exif.get_ifd(0x8769) or {}
            except Exception:
                ifd = {}
            captured = _parse_exif_date(exif.get(36867) or ifd.get(36867) or exif.get(306))
            description = str(exif.get(270) or "").strip()
            gps_ifd = {}
            try:
                gps_ifd = exif.get_ifd(34853) or {}
            except Exception:
                gps_ifd = {}
            lat = _to_degrees(gps_ifd.get(2))
            lon = _to_degrees(gps_ifd.get(4))
            if lat is not None and lon is not None:
                if str(gps_ifd.get(1, "N")).upper().startswith("S"):
                    lat = -lat
                if str(gps_ifd.get(3, "E")).upper().startswith("W"):
                    lon = -lon
                gps = [round(lat, 6), round(lon, 6)]
    except Exception:
        pass
    if captured is None:
        captured = datetime.datetime.fromtimestamp(path.stat().st_mtime)
    return captured, description, gps


def season_of(month):
    if month in (3, 4, 5):
        return "春"
    if month in (6, 7, 8):
        return "夏"
    if month in (9, 10, 11):
        return "秋"
    return "冬"


def dhash(image, size=8):
    """给以后做相似照片聚类留的指纹，当前只写进数据，不自动合并。"""
    gray = image.convert("L").resize((size + 1, size), Image.LANCZOS)
    pixels = list(gray.getdata())
    bits = 0
    for row in range(size):
        for col in range(size):
            left = pixels[row * (size + 1) + col]
            right = pixels[row * (size + 1) + col + 1]
            bits = (bits << 1) | (1 if left > right else 0)
    return "%016x" % bits


def scan(root, out, copy_originals=False, limit=None, progress=None):
    root = Path(root).resolve()
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    thumb_dir = out / "thumbs"
    thumb_dir.mkdir(exist_ok=True)
    original_dir = out / "originals"
    if copy_originals:
        original_dir.mkdir(exist_ok=True)

    photos = []
    seen = {}
    duplicates = 0
    files = sorted((path for path in root.rglob("*") if path.suffix.lower() in EXTENSIONS),
                   key=lambda path: (any(token in path.stem.lower() for token in ("副本", "copy")), str(path)))
    if limit:
        files = files[:limit]
    for index, path in enumerate(files, 1):
        if out in path.parents or path == out:
            continue
        if progress:
            progress(index, len(files), path.name)
        digest = sha256(path)
        if digest in seen:
            seen[digest]["duplicate_count"] += 1
            duplicates += 1
            continue
        captured, description, gps = read_metadata(path)
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                width, height = image.size
                thumb = image.copy()
                thumb.thumbnail((520, 520), Image.LANCZOS)
                thumb_name = digest[:16] + ".jpg"
                thumb.save(thumb_dir / thumb_name, "JPEG", quality=84, optimize=True)
                fingerprint = dhash(image)
        except Exception:
            continue
        full = ""
        if copy_originals:
            full_name = digest[:16] + path.suffix.lower()
            shutil.copy2(path, original_dir / full_name)
            full = "originals/" + full_name
        album_parts = list(path.relative_to(root).parent.parts)
        album = " / ".join(album_parts) if album_parts else "未分类"
        if "?" in description:
            description = ""
        caption = description or path.stem.replace("_", " ").replace("-", " ").strip()
        entry = {
            "id": index,
            "file": path.name,
            "rel": str(path.relative_to(root)),
            "thumb": "thumbs/" + thumb_name,
            "full": full,
            "caption": caption,
            "album": album,
            "date": captured.strftime("%Y-%m-%d %H:%M"),
            "year": captured.year,
            "month": captured.month,
            "season": season_of(captured.month),
            "width": width,
            "height": height,
            "gps": gps,
            "hash": digest,
            "dhash": fingerprint,
            "duplicate_count": 0,
        }
        seen[digest] = entry
        photos.append(entry)

    photos.sort(key=lambda item: (item["date"], item["file"]))
    exhibitions = build_exhibitions(photos)
    years = sorted({photo["year"] for photo in photos}, reverse=True)
    stats = {
        "photos": len(photos),
        "duplicates": duplicates,
        "years": years,
        "year_span": ("%d–%d" % (min(years), max(years))) if years else "—",
        "places": len({tuple(photo["gps"]) for photo in photos if photo["gps"]}),
    }
    data = {"title": "", "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
            "stats": stats, "photos": photos, "exhibitions": exhibitions}
    return data


def build_exhibitions(photos):
    groups = {}
    for photo in photos:
        key = "%d-%s" % (photo["year"], photo["season"])
        groups.setdefault(key, []).append(photo)
    exhibitions = []
    for key, items in groups.items():
        items.sort(key=lambda item: item["date"])
        exhibitions.append({
            "key": key,
            "title": "%d · %s" % (items[0]["year"], items[0]["season"]),
            "subtitle": "%d 年 %d–%d 月" % (items[0]["year"], min(i["month"] for i in items),
                                            max(i["month"] for i in items)),
            "count": len(items),
            "cover": items[0]["thumb"],
            "from": items[0]["date"],
            "to": items[-1]["date"],
        })
    exhibitions.sort(key=lambda item: item["key"], reverse=True)
    return exhibitions


def write_site(data, out, title):
    out = Path(out).resolve()
    data["title"] = title
    (out / "data.js").write_text("window.MUSEUM = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
                                 encoding="utf-8")
    web = Path(__file__).resolve().parent / "web"
    for name in ("index.html", "style.css", "app.js"):
        shutil.copy2(web / name, out / name)
    (out / "index.html").write_text(
        (web / "index.html").read_text(encoding="utf-8").replace("{{TITLE}}", title),
        encoding="utf-8")
    return out / "index.html"
