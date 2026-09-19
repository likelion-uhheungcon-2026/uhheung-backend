import json
import os
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from booths.models import Booth

FIELDS = ["refactoring", "collaboration", "message"]


class Command(BaseCommand):
    help = "회고 파일(RETROSPECT_URL 또는 data/retrospects.json)의 세 항목만 기존 부스에 덮어쓴다. 조회 기록은 건드리지 않는다."

    def handle(self, *args, **options):
        url = os.environ.get("RETROSPECT_URL")

        if url:
            with urllib.request.urlopen(url) as response:
                items = json.loads(response.read().decode("utf-8"))
            source = url
        elif settings.RETROSPECT_FILE.exists():
            items = json.loads(settings.RETROSPECT_FILE.read_text(encoding="utf-8"))
            source = settings.RETROSPECT_FILE
        else:
            self.stdout.write("회고 파일이 없어 건너뜁니다.")
            return

        updated = 0
        with transaction.atomic():
            for item in items:
                updated += Booth.objects.filter(pk=item["id"]).update(
                    **{field: item.get(field) or "" for field in FIELDS}
                )

        self.stdout.write(self.style.SUCCESS(f"부스 {updated}건 회고 갱신 완료. ({source})"))
