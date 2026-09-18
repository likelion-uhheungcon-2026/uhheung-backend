import io
import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image

from booths.models import BoothImage

SOURCES = {
    1: ("Aftor_국경없는사자들(5)", "Aftor_국경없는사자들_로고"),
    2: ("travel_main", None),
    3: ("시원쿨쿨멋터밤_picknu_1", "시원쿨쿨멋터밤_picknu_로고"),
    4: ("MCM_Orbit_대표사진", "MCM Orbit Logo"),
    5: ("MCM Time portal_하이파이브", None),
    6: ("NEXTiME_회고자료_정사각형", "NEXTiME LOGO"),
    7: ("AfterGrow_삶이순탄쿠나_1", "AfterGrow_삶이순탄쿠나_로고"),
    8: ("REFIT_왕꿈트리 -", "REFIT_왕꿈트리_로고"),
    9: ("눈눈_이리저리 - 김혜윤.", "눈눈_이리저리_로고"),
    10: ("momote_수상한아기사자들 -", "momote_수상한아기사자들_로고"),
    11: ("MXIS_더버버 -", "MXIS_더버버_로고"),
    12: ("서비스 대표 이미지_SKINEARTH", "서비스 로고 이미지_SKINEARTH"),
    13: ("SOTT_영크크 말고 봉크크 -", "SOTT_영크크 말고 봉크크_로고"),
    14: ("대표사진 - 배세은", "스티커 - 배세은"),
    15: ("HALE_오리스웰 -", "HALE_오리스웰_로고"),
    16: ("CLOSER_초코숭이 -", "CLOSER_초코숭이_로고"),
    17: ("AURA_독수리6형제 -", "AURA_독수리6형제_로고"),
    18: ("TagonAI_사춘기온사자_표지 - 정난꾸.", "TagonAI_사춘기온사자_로고 - 정난꾸."),
    19: ("MCM LOUNGE_되면천재안되면쩔수 -", "MCM LOUNGE_되면천재안되면쩔수_로고"),
    20: ("서비스 대표 이미지 - [10반]박형진", None),
    21: ("IMG_4565 - minkq", None),
}


class Command(BaseCommand):
    help = "부스 대표 이미지와 로고를 웹용 PNG 로 줄여 DB 에 넣는다."

    def add_arguments(self, parser):
        parser.add_argument("--images", required=True, help="대표 이미지 원본 폴더")
        parser.add_argument("--logos", required=True, help="로고 이미지 원본 폴더")

    def handle(self, *args, **options):
        images_dir = Path(options["images"])
        logos_dir = Path(options["logos"])

        for directory in (images_dir, logos_dir):
            if not directory.is_dir():
                raise CommandError(f"폴더가 없습니다: {directory}")

        image_files = sorted(p.name for p in images_dir.iterdir() if p.is_file())
        logo_files = sorted(p.name for p in logos_dir.iterdir() if p.is_file())

        total = 0
        with transaction.atomic():
            for booth_id, (image_prefix, logo_prefix) in sorted(SOURCES.items()):
                source = images_dir / self._pick(image_files, image_prefix, booth_id, "대표")
                service_image = self._convert(source, settings.BOOTH_IMAGE_WIDTH)

                logo_image = None
                if logo_prefix:
                    logo_source = logos_dir / self._pick(logo_files, logo_prefix, booth_id, "로고")
                    logo_image = self._convert(logo_source, settings.BOOTH_LOGO_WIDTH)

                BoothImage.objects.update_or_create(
                    booth_id=booth_id,
                    defaults={"service_image": service_image, "logo_image": logo_image},
                )

                total += len(service_image) + len(logo_image or b"")
                self.stdout.write(
                    f"{booth_id:>2}번 대표 {len(service_image) // 1024}KB"
                    f" / 로고 {len(logo_image) // 1024 if logo_image else '-'}KB"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"부스 {len(SOURCES)}개 이미지를 DB 에 저장했습니다. (총 {total // 1024 // 1024}MB)"
            )
        )

    def _pick(self, names, prefix, booth_id, label):
        wanted = unicodedata.normalize("NFC", prefix)
        matches = [
            name for name in names if unicodedata.normalize("NFC", name).startswith(wanted)
        ]
        if len(matches) != 1:
            raise CommandError(
                f"{booth_id}번 {label} 원본을 특정할 수 없습니다. "
                f"prefix={prefix!r} matches={matches}"
            )
        return matches[0]

    def _convert(self, source, width):
        with Image.open(source) as image:
            image = image.convert("RGBA")
            if image.width > width:
                height = round(image.height * width / image.width)
                image = image.resize((width, height), Image.LANCZOS)

            buffer = io.BytesIO()
            image.save(buffer, "PNG", optimize=True)

        return buffer.getvalue()
