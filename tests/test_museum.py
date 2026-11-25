# -*- coding: utf-8 -*-
import datetime
import json
import shutil

from PIL import Image

from family_museum.build import build_exhibitions, scan, season_of, write_site


def make_image(path, color=(80, 120, 160), when=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (320, 240), color).save(path, "JPEG")
    if when:
        stamp = when.timestamp()
        import os
        os.utime(path, (stamp, stamp))


def test_scan_builds_museum(tmp_path):
    photos = tmp_path / "photos"
    make_image(photos / "2019" / "夏" / "海边.jpg", when=datetime.datetime(2019, 7, 20, 10, 0))
    make_image(photos / "2021" / "冬" / "雪.jpg", (180, 180, 190), datetime.datetime(2021, 1, 6, 9, 0))
    make_image(photos / "2021" / "夏" / "搬家.jpg", (150, 120, 90), datetime.datetime(2021, 6, 12, 14, 0))
    out = tmp_path / "museum"
    data = scan(photos, out, copy_originals=True, limit=None)
    assert data["stats"]["photos"] == 3
    assert data["stats"]["duplicates"] == 0
    assert len(data["exhibitions"]) == 3
    page = write_site(data, out, "测试的家")
    assert page.exists()
    text = page.read_text(encoding="utf-8")
    assert "测试的家" in text
    assert len(list((out / "thumbs").glob("*.jpg"))) == 3
    assert len(list((out / "originals").glob("*"))) == 3
    entries = json.loads((out / "data.js").read_text(encoding="utf-8").split("=", 1)[1].strip().rstrip(";"))
    assert entries["title"] == "测试的家"
    assert entries["photos"][0]["full"].startswith("originals/")


def test_exact_duplicate_is_skipped_and_counted(tmp_path):
    photos = tmp_path / "photos"
    original = photos / "2019" / "海边.jpg"
    make_image(original, when=datetime.datetime(2019, 7, 20, 10, 0))
    shutil.copy2(original, photos / "2019" / "海边-副本.jpg")
    data = scan(photos, tmp_path / "museum", copy_originals=False)
    assert data["stats"]["photos"] == 1
    assert data["stats"]["duplicates"] == 1
    assert data["photos"][0]["file"] == "海边.jpg"
    assert data["photos"][0]["duplicate_count"] == 1


def test_season_and_exhibitions():
    assert season_of(3) == "春"
    assert season_of(6) == "夏"
    assert season_of(9) == "秋"
    assert season_of(12) == "冬"
    photos = [
        {"year": 2019, "season": "夏", "month": 7, "date": "2019-07-01 10:00", "thumb": "a.jpg"},
        {"year": 2019, "season": "夏", "month": 8, "date": "2019-08-01 10:00", "thumb": "b.jpg"},
        {"year": 2020, "season": "冬", "month": 1, "date": "2020-01-01 10:00", "thumb": "c.jpg"},
    ]
    exhibitions = build_exhibitions(photos)
    assert exhibitions[0]["key"] == "2020-冬"
    summer = [item for item in exhibitions if item["key"] == "2019-夏"][0]
    assert summer["count"] == 2
    assert summer["cover"] == "a.jpg"
