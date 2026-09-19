from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from booths.models import Booth, BoothLink
from booths.release_data import load_release_data


class Command(BaseCommand):
    help = "링크 파일(LINKS_URL 또는 data/links.json)의 서비스·GitHub·Figma·기타 링크만 기존 부스에 덮어쓴다. 조회 기록은 건드리지 않는다."

    def handle(self, *args, **options):
        items, source = load_release_data("LINKS_URL", settings.LINKS_FILE)
        if items is None:
            self.stdout.write("링크 파일이 없어 건너뜁니다.")
            return

        updated = 0
        with transaction.atomic():
            for item in items:
                booth = Booth.objects.filter(pk=item["id"]).first()
                if booth is None:
                    continue

                links = {kind: item.get(f"{kind}links") or [] for kind in BoothLink.KINDS}

                booth.service_link = next(iter(links["service"]), None)
                booth.github_link = next(iter(links["github"]), None)
                booth.figma_link = next(iter(links["figma"]), None)
                booth.save(update_fields=["service_link", "github_link", "figma_link"])

                booth.links.all().delete()
                BoothLink.objects.bulk_create(
                    BoothLink(booth=booth, kind=kind, position=position, url=url)
                    for kind, urls in links.items()
                    for position, url in enumerate(urls)
                )
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"부스 {updated}건 링크 갱신 완료. ({source})"))
