import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCES_FILE = BASE_DIR / "data" / "photo_sources.json"
PHOTOS_FILE = BASE_DIR / "data" / "photos.zip"
WIDTH = 1200
QUALITY = 80


def convert(path):
    with Image.open(path) as image:
        image = image.convert("RGBA")
        if image.width > WIDTH:
            image = image.resize((WIDTH, round(image.height * WIDTH / image.width)), Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, "WEBP", quality=QUALITY, method=6)
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description="부스 이미지를 WebP로 줄여 data/photos.zip 으로 묶는다.")
    parser.add_argument("--images", type=Path, required=True, help="서비스 대표 이미지 원본 폴더")
    args = parser.parse_args()

    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    manifest, total = {}, 0

    with zipfile.ZipFile(PHOTOS_FILE, "w", zipfile.ZIP_STORED) as archive:
        for booth_id, names in sorted(sources.items(), key=lambda item: int(item[0])):
            manifest[booth_id] = []
            for name in names:
                try:
                    data = convert(args.images / name)
                except (OSError, ValueError) as error:
                    print(f"{int(booth_id):>2}번 이미지를 열 수 없어 건너뜀: {name} ({error})")
                    continue
                entry = f"{booth_id}_{len(manifest[booth_id])}.webp"
                archive.writestr(entry, data)
                manifest[booth_id].append(entry)
                total += len(data)
            print(f"{int(booth_id):>2}번 {len(manifest[booth_id])}장")

        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    count = sum(len(entries) for entries in manifest.values())
    print(f"이미지 {count}장, {total // 1024}KB → {PHOTOS_FILE} (깃에 올리지 않음, 릴리즈로 업로드)")


if __name__ == "__main__":
    sys.exit(main())
