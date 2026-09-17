from rest_framework import serializers

from .models import Booth


class BoothSummarySerializer(serializers.ModelSerializer):
    maincontent = serializers.CharField(source="main_content")
    serviceimage = serializers.CharField(source="service_image", allow_null=True)
    servicelink = serializers.CharField(source="service_link", allow_null=True)
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
            "maincontent",
            "serviceimage",
            "servicelink",
            "recommendScore",
            "viewCount",
            "visitorCount",
            "totalDurationMs",
            "avgDurationMs",
        ]


class BoothDetailSerializer(BoothSummarySerializer):
    githublink = serializers.CharField(source="github_link", allow_null=True)
    figmalink = serializers.CharField(source="figma_link", allow_null=True)
    function = serializers.SerializerMethodField()
    techstack = serializers.SerializerMethodField()

    class Meta(BoothSummarySerializer.Meta):
        fields = BoothSummarySerializer.Meta.fields + [
            "content",
            "retrospect",
            "githublink",
            "figmalink",
            "function",
            "techstack",
        ]

    def get_function(self, booth):
        return [item.content for item in booth.functions.all()]

    def get_techstack(self, booth):
        return [item.content for item in booth.tech_stack.all()]
