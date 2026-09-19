import io
import json
import zipfile

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from booths.models import Booth, BoothImage, BoothPhoto
from booths.release_data import load_release_bytes


class Command(BaseCommand):
    help = "이미지 묶음(PHOTOS_URL 또는 data/photos.zip)으로 부스 이미지를 덮어쓴다. 첫 장이 대표 이미지. 조회 기록은 건드리지 않는다."

    def handle(self, *args, **options):
        data, source = load_release_bytes("PHOTOS_URL", settings.PHOTOS_FILE)
        if data is None:
            self.stdout.write("이미지 묶음이 없어 건너뜁니다.")
            return

        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        except (zipfile.BadZipFile, KeyError, ValueError) as error:
            self.stderr.write(f"{source} 형식이 올바르지 않아 건너뜁니다: {error}")
            return

        booths = set(Booth.objects.values_list("id", flat=True))
        updated = count = 0

        with transaction.atomic():
            for booth_id, entries in manifest.items():
                booth_id = int(booth_id)
                if booth_id not in booths or not entries:
                    continue

                images = [archive.read(entry) for entry in entries]

                BoothPhoto.objects.filter(booth_id=booth_id).delete()
                BoothPhoto.objects.bulk_create(
                    BoothPhoto(booth_id=booth_id, position=position, image=image)
                    for position, image in enumerate(images)
                )

                cover, _ = BoothImage.objects.get_or_create(booth_id=booth_id)
                cover.service_image = images[0]
                cover.save()

                updated += 1
                count += len(images)

        self.stdout.write(
            self.style.SUCCESS(f"부스 {updated}건 이미지 {count}장 갱신 완료. ({source})")
        )
