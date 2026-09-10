from django.conf import settings
from django.db import models


class Booth(models.Model):
    """출품작 부스 하나."""

    # 시드 데이터의 부스 번호를 그대로 쓴다. 프론트 지도의 좌석 번호와 같은 값.
    id = models.IntegerField(primary_key=True, verbose_name="부스 번호")

    name = models.CharField(max_length=100, verbose_name="서비스명")
    team = models.CharField(max_length=100, verbose_name="팀명")
    tag = models.CharField(
        max_length=10,
        choices=[(tag, tag) for tag in settings.BOOTH_TAGS],
        db_index=True,
        verbose_name="분류",
    )

    main_content = models.TextField(blank=True, default="", verbose_name="한 줄 소개")
    content = models.TextField(blank=True, default="", verbose_name="상세 설명")
    retrospect = models.TextField(blank=True, default="", verbose_name="회고")

    service_image = models.CharField(max_length=300, blank=True, null=True)
    service_link = models.CharField(max_length=300, blank=True, null=True)
    github_link = models.CharField(max_length=300, blank=True, null=True)
    figma_link = models.CharField(max_length=300, blank=True, null=True)

    # '추천 순' 정렬용 가중치. 운영진이 손으로 올려주는 값이며 기본 0.
    recommend_score = models.IntegerField(default=0, verbose_name="추천 가중치")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booth"
        ordering = ["id"]
        verbose_name = "부스"
        verbose_name_plural = "부스"

    def __str__(self):
        return f"{self.id}번 {self.name}"


class BoothFunction(models.Model):
    """부스별 주요 기능 한 줄."""

    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="functions")
    position = models.IntegerField()
    content = models.CharField(max_length=200)

    class Meta:
        db_table = "booth_function"
        ordering = ["position"]
        unique_together = [("booth", "position")]


class BoothTechStack(models.Model):
    """부스별 기술 스택 한 줄."""

    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="tech_stack")
    position = models.IntegerField()
    content = models.CharField(max_length=200)

    class Meta:
        db_table = "booth_tech_stack"
        ordering = ["position"]
        unique_together = [("booth", "position")]


class BoothView(models.Model):
    """방문자 한 명이 부스 상세를 한 번 열어본 기록.

    집계 대신 원본 로그를 쌓아두면 나중에 시간대별 분석 같은 것도 할 수 있다.
    """

    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="views")
    # 로그인이 없으므로 프론트가 localStorage 에 만들어 보관하는 익명 UUID
    visitor_id = models.CharField(max_length=64, db_index=True)
    duration_ms = models.PositiveIntegerField(default=0)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booth_view"
        indexes = [models.Index(fields=["booth", "viewed_at"])]
