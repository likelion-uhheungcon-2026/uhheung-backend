from rest_framework import serializers

from .models import Booth

# 프론트가 쓰는 이름에 맞춰 camelCase 로 내려보낸다.


class BoothSummarySerializer(serializers.ModelSerializer):
    """목록 카드용. 상세 본문(content/retrospect)은 빼서 응답을 가볍게 유지한다."""

    mainContent = serializers.CharField(source="main_content")
    serviceImage = serializers.CharField(source="service_image", allow_null=True)
    serviceLink = serializers.CharField(source="service_link", allow_null=True)
    recommendScore = serializers.IntegerField(source="recommend_score")

    viewCount = serializers.IntegerField(source="view_count")
    visitorCount = serializers.IntegerField(source="visitor_count")
    totalDurationMs = serializers.IntegerField(source="total_duration_ms")
    avgDurationMs = serializers.IntegerField(source="avg_duration_ms")

    class Meta:
        model = Booth
        fields = [
            "id",
            "name",
            "team",
            "tag",
            "mainContent",
            "serviceImage",
            "serviceLink",
            "recommendScore",
            "viewCount",
            "visitorCount",
            "totalDurationMs",
            "avgDurationMs",
        ]


class BoothDetailSerializer(BoothSummarySerializer):
    githubLink = serializers.CharField(source="github_link", allow_null=True)
    figmaLink = serializers.CharField(source="figma_link", allow_null=True)
    functions = serializers.SerializerMethodField()
    techStack = serializers.SerializerMethodField()

    class Meta(BoothSummarySerializer.Meta):
        fields = BoothSummarySerializer.Meta.fields + [
            "content",
            "retrospect",
            "githubLink",
            "figmaLink",
            "functions",
            "techStack",
        ]

    def get_functions(self, booth):
        return [item.content for item in booth.functions.all()]

    def get_techStack(self, booth):  # noqa: N802 - 프론트 필드명에 맞춘다
        return [item.content for item in booth.tech_stack.all()]
