from rest_framework import serializers

from .models import Booth


class BoothSummarySerializer(serializers.ModelSerializer):
    maincontent = serializers.CharField(source="main_content")
    serviceimage = serializers.SerializerMethodField()
    logoimage = serializers.SerializerMethodField()
    servicelink = serializers.CharField(source="service_link", allow_null=True)
    recommendScore = serializers.IntegerField(source="recommend_score")

    viewCount = serializers.IntegerField(source="view_count")
    recentViewCount = serializers.IntegerField(source="recent_view_count")
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
            "logoimage",
            "servicelink",
            "recommendScore",
            "viewCount",
            "recentViewCount",
            "visitorCount",
            "totalDurationMs",
            "avgDurationMs",
        ]

    def _image_url(self, booth, suffix):
        url = f"/api/booths/{booth.id}/{suffix}"
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_serviceimage(self, booth):
        if getattr(booth, "has_service_image", False):
            return self._image_url(booth, "image")
        return booth.service_image or None

    def get_logoimage(self, booth):
        if getattr(booth, "has_logo_image", False):
            return self._image_url(booth, "logo")
        return None


class BoothDetailSerializer(BoothSummarySerializer):
    githublink = serializers.CharField(source="github_link", allow_null=True)
    figmalink = serializers.CharField(source="figma_link", allow_null=True)
    function = serializers.SerializerMethodField()
    techstack = serializers.SerializerMethodField()
    servicelinks = serializers.SerializerMethodField()
    githublinks = serializers.SerializerMethodField()
    figmalinks = serializers.SerializerMethodField()
    etclinks = serializers.SerializerMethodField()

    class Meta(BoothSummarySerializer.Meta):
        fields = BoothSummarySerializer.Meta.fields + [
            "content",
            "refactoring",
            "collaboration",
            "message",
            "githublink",
            "figmalink",
            "servicelinks",
            "githublinks",
            "figmalinks",
            "etclinks",
            "function",
            "techstack",
        ]

    def get_function(self, booth):
        return [item.content for item in booth.functions.all()]

    def get_techstack(self, booth):
        return [item.content for item in booth.tech_stack.all()]

    def _links(self, booth, kind):
        return [link.url for link in booth.links.all() if link.kind == kind]

    def get_servicelinks(self, booth):
        return self._links(booth, "service")

    def get_githublinks(self, booth):
        return self._links(booth, "github")

    def get_figmalinks(self, booth):
        return self._links(booth, "figma")

    def get_etclinks(self, booth):
        return self._links(booth, "etc")
