from django.conf import settings
from django.db import models


class Booth(models.Model):
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
    refactoring = models.TextField(blank=True, default="", verbose_name="서비스 리팩토링 내용")
    collaboration = models.TextField(blank=True, default="", verbose_name="우리 팀의 협업 이야기")
    message = models.TextField(blank=True, default="", verbose_name="서로에게 전하는 한 마디")

    service_image = models.CharField(max_length=300, blank=True, null=True)
    service_link = models.CharField(max_length=300, blank=True, null=True)
    github_link = models.CharField(max_length=300, blank=True, null=True)
    figma_link = models.CharField(max_length=300, blank=True, null=True)

    recommend_score = models.IntegerField(default=0, verbose_name="추천 가중치")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booth"
        ordering = ["id"]
        verbose_name = "부스"
        verbose_name_plural = "부스"

    def __str__(self):
        return f"{self.id}번 {self.name}"


class BoothImage(models.Model):
    booth_id = models.IntegerField(primary_key=True, verbose_name="부스 번호")

    service_image = models.BinaryField(blank=True, null=True, verbose_name="대표 이미지")
    logo_image = models.BinaryField(blank=True, null=True, verbose_name="로고 이미지")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booth_image"
        ordering = ["booth_id"]
        verbose_name = "부스 이미지"
        verbose_name_plural = "부스 이미지"

    def __str__(self):
        return f"{self.booth_id}번 이미지"


class BoothPhoto(models.Model):
    booth = models.ForeignKey(
        Booth, on_delete=models.DO_NOTHING, db_constraint=False, related_name="photos"
    )
    position = models.IntegerField()
    image = models.BinaryField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booth_photo"
        ordering = ["position"]
        unique_together = [("booth", "position")]


class BoothFunction(models.Model):
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="functions")
    position = models.IntegerField()
    content = models.CharField(max_length=200)

    class Meta:
        db_table = "booth_function"
        ordering = ["position"]
        unique_together = [("booth", "position")]


class BoothTechStack(models.Model):
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="tech_stack")
    position = models.IntegerField()
    content = models.CharField(max_length=200)

    class Meta:
        db_table = "booth_tech_stack"
        ordering = ["position"]
        unique_together = [("booth", "position")]


class BoothLink(models.Model):
    KINDS = ["service", "github", "figma", "etc"]

    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="links")
    kind = models.CharField(max_length=10, choices=[(kind, kind) for kind in KINDS])
    position = models.IntegerField()
    url = models.CharField(max_length=500)

    class Meta:
        db_table = "booth_link"
        ordering = ["kind", "position"]
        unique_together = [("booth", "kind", "position")]


class BoothView(models.Model):
    booth = models.ForeignKey(Booth, on_delete=models.CASCADE, related_name="views")
    visitor_id = models.CharField(max_length=64, db_index=True)
    duration_ms = models.PositiveIntegerField(default=0)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booth_view"
        indexes = [models.Index(fields=["booth", "viewed_at"])]
