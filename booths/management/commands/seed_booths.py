"""data/booths.seed.json 의 부스 데이터를 DB 에 밀어 넣는다.

실행할 때마다 booth 테이블을 비우고 다시 채우므로 언제든 되돌릴 수 있다.

    python manage.py seed_booths                부스 데이터만
    python manage.py seed_booths --with-views   + 로컬 확인용 가짜 조회 로그
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from booths.models import Booth, BoothFunction, BoothTechStack, BoothView


class Command(BaseCommand):
    help = "부스 시드 데이터를 DB 에 넣는다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-views",
            action="store_true",
            help="인기 순/랭킹을 로컬에서 확인하기 위한 가짜 조회 로그도 만든다.",
        )

    def handle(self, *args, **options):
        with_views = options["with_views"]

        if not settings.SEED_FILE.exists():
            raise CommandError(f"시드 파일이 없습니다: {settings.SEED_FILE}")

        booths = json.loads(settings.SEED_FILE.read_text(encoding="utf-8"))

        with transaction.atomic():
            # FK 가 CASCADE 이므로 booth 만 지우면 자식 테이블도 함께 정리된다.
            Booth.objects.all().delete()

            for index, item in enumerate(booths):
                self._validate(item, index)

                booth = Booth.objects.create(
                    id=item["id"],
                    name=item["name"],
                    team=item["team"],
                    tag=item["tag"],
                    main_content=item.get("mainContent") or "",
                    content=item.get("content") or "",
                    retrospect=item.get("retrospect") or "",
                    service_image=item.get("serviceImage"),
                    service_link=item.get("serviceLink"),
                    github_link=item.get("githubLink"),
                    figma_link=item.get("figmaLink"),
                    recommend_score=item.get("recommendScore", 0),
                )

                BoothFunction.objects.bulk_create(
                    BoothFunction(booth=booth, position=position, content=content)
                    for position, content in enumerate(item.get("functions") or [])
                )

                BoothTechStack.objects.bulk_create(
                    BoothTechStack(booth=booth, position=position, content=content)
                    for position, content in enumerate(item.get("techStack") or [])
                )

            if with_views:
                self._seed_views(booths)

        total = Booth.objects.count()
        views = BoothView.objects.count()

        self.stdout.write(self.style.SUCCESS(f"부스 {total}건 시드 완료."))
        self.stdout.write(
            f"데모 조회 로그 {views}건 생성."
            if with_views
            else "조회 로그는 생성하지 않았습니다."
        )

    def _validate(self, item, index):
        booth_id = item.get("id")
        if not isinstance(booth_id, int) or booth_id < 1:
            raise CommandError(f"[{index}] id 가 올바르지 않습니다: {booth_id}")

        if not item.get("name") or not item.get("team"):
            raise CommandError(f"[{index}] name / team 은 필수입니다. (id={booth_id})")

        if item.get("tag") not in settings.BOOTH_TAGS:
            raise CommandError(
                f"[{index}] tag 는 {', '.join(settings.BOOTH_TAGS)} 중 하나여야 합니다. "
                f"(id={booth_id}, tag={item.get('tag')})"
            )

    def _seed_views(self, booths):
        """앞쪽 부스일수록 조회수가 많게 만들어 정렬 결과를 눈으로 구분할 수 있게 한다."""
        logs = []
        for item in booths:
            booth_id = item["id"]
            count = max(1, 40 - booth_id)
            for i in range(count):
                logs.append(
                    BoothView(
                        booth_id=booth_id,
                        visitor_id=f"demo-visitor-{i % 12}",
                        duration_ms=3000 + ((booth_id * 7 + i * 13) % 60_000),
                    )
                )

        BoothView.objects.bulk_create(logs)
