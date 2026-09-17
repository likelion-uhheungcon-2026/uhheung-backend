import math
from datetime import datetime, timezone

from django.conf import settings
from django.db.models import Avg, Count, Exists, IntegerField, OuterRef, Q, Sum, Value
from django.db.models.functions import Cast, Coalesce
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import ApiError
from .models import Booth, BoothImage, BoothView
from .params import parse_enum, parse_enum_list, parse_integer, parse_string
from .serializers import BoothDetailSerializer, BoothSummarySerializer

SORTS = {
    "id": ["id"],
    "name": ["name", "id"],
    "popular": ["-view_count", "-total_duration_ms", "id"],
    "recommend": ["-recommend_score", "-view_count", "id"],
}

RANKING_METRICS = {
    "views": ["-view_count", "-total_duration_ms", "id"],
    "duration": ["-total_duration_ms", "-view_count", "id"],
    "avgDuration": ["-avg_duration_ms", "-view_count", "id"],
}


def with_stats(queryset):
    return queryset.annotate(
        view_count=Count("views"),
        visitor_count=Count("views__visitor_id", distinct=True),
        total_duration_ms=Coalesce(Sum("views__duration_ms"), Value(0)),
        avg_duration_ms=Cast(
            Coalesce(Avg("views__duration_ms"), Value(0.0)), IntegerField()
        ),
        has_service_image=Exists(
            BoothImage.objects.filter(booth_id=OuterRef("pk"), service_image__isnull=False)
        ),
        has_logo_image=Exists(
            BoothImage.objects.filter(booth_id=OuterRef("pk"), logo_image__isnull=False)
        ),
    )


def stat_payload(booth_id):
    booth = with_stats(Booth.objects.filter(pk=booth_id)).first()
    if booth is None:
        return None

    return {
        "boothId": booth.id,
        "viewCount": booth.view_count,
        "visitorCount": booth.visitor_count,
        "totalDurationMs": booth.total_duration_ms,
        "avgDurationMs": booth.avg_duration_ms,
    }


def health(request):
    return JsonResponse(
        {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


class BoothListView(APIView):
    def get(self, request):
        query = request.query_params

        search = parse_string(query.get("search"), field="search", max_length=100)
        tags = parse_enum_list(query.get("tags"), field="tags", allowed=settings.BOOTH_TAGS)
        sort = parse_enum(query.get("sort"), field="sort", allowed=list(SORTS), fallback="name")
        page = parse_integer(query.get("page"), field="page", minimum=1, maximum=10_000, fallback=1)
        size = parse_integer(
            query.get("size"),
            field="size",
            minimum=1,
            maximum=settings.MAX_PAGE_SIZE,
            fallback=settings.DEFAULT_PAGE_SIZE,
        )
        detail = parse_integer(query.get("detail"), field="detail", minimum=0, maximum=1, fallback=0) == 1

        booths = Booth.objects.all()

        if search:
            booths = booths.filter(
                Q(name__icontains=search)
                | Q(team__icontains=search)
                | Q(main_content__icontains=search)
            )

        if tags:
            booths = booths.filter(tag__in=tags)

        total = booths.count()
        offset = (page - 1) * size
        items = with_stats(booths).order_by(*SORTS[sort])
        if detail:
            items = items.prefetch_related("functions", "tech_stack")
        items = items[offset : offset + size]
        serializer = BoothDetailSerializer if detail else BoothSummarySerializer

        return Response(
            {
                "items": serializer(items, many=True, context={"request": request}).data,
                "page": page,
                "size": size,
                "total": total,
                "totalPages": math.ceil(total / size),
            }
        )


class BoothTagListView(APIView):
    def get(self, request):
        counts = dict(
            Booth.objects.values_list("tag").annotate(count=Count("id")).values_list("tag", "count")
        )

        return Response(
            {"items": [{"tag": tag, "count": counts.get(tag, 0)} for tag in settings.BOOTH_TAGS]}
        )


class BoothRankingView(APIView):
    def get(self, request):
        metric = parse_enum(
            request.query_params.get("metric"),
            field="metric",
            allowed=list(RANKING_METRICS),
            fallback="views",
        )
        limit = parse_integer(
            request.query_params.get("limit"), field="limit", minimum=1, maximum=20, fallback=3
        )

        items = with_stats(Booth.objects.all()).order_by(*RANKING_METRICS[metric])[:limit]

        return Response(
            {
                "metric": metric,
                "items": BoothSummarySerializer(
                    items, many=True, context={"request": request}
                ).data,
            }
        )


class BoothDetailView(APIView):
    def get(self, request, booth_id):
        booth = (
            with_stats(Booth.objects.filter(pk=booth_id))
            .prefetch_related("functions", "tech_stack")
            .first()
        )

        if booth is None:
            raise ApiError.not_found(f"{booth_id}번 부스를 찾을 수 없습니다.", "BOOTH_NOT_FOUND")

        return Response(BoothDetailSerializer(booth, context={"request": request}).data)


class BoothImageView(APIView):
    field = "service_image"

    def get(self, request, booth_id):
        image = BoothImage.objects.filter(booth_id=booth_id).only(self.field).first()
        data = getattr(image, self.field, None) if image else None

        if not data:
            raise ApiError.not_found(
                f"{booth_id}번 부스의 이미지를 찾을 수 없습니다.", "BOOTH_IMAGE_NOT_FOUND"
            )

        response = HttpResponse(bytes(data), content_type="image/png")
        response["Cache-Control"] = "public, max-age=86400"
        return response


class BoothLogoView(BoothImageView):
    field = "logo_image"


class BoothViewLogView(APIView):
    def _require_booth(self, booth_id):
        if not Booth.objects.filter(pk=booth_id).exists():
            raise ApiError.not_found(f"{booth_id}번 부스를 찾을 수 없습니다.", "BOOTH_NOT_FOUND")

    def get(self, request, booth_id):
        self._require_booth(booth_id)
        return Response(stat_payload(booth_id))

    def post(self, request, booth_id):
        self._require_booth(booth_id)
        body = request.data if isinstance(request.data, dict) else {}

        visitor_id = parse_string(body.get("visitorId"), field="visitorId", max_length=64)
        if not visitor_id:
            raise ApiError.bad_request("visitorId 는 필수입니다.", "VISITOR_ID_REQUIRED")

        raw_duration = body.get("durationMs", 0)
        if isinstance(raw_duration, bool) or not isinstance(raw_duration, (int, float)):
            raise ApiError.bad_request(
                "durationMs 는 0 이상의 숫자여야 합니다.", "INVALID_DURATION"
            )
        if raw_duration < 0 or raw_duration != raw_duration:
            raise ApiError.bad_request(
                "durationMs 는 0 이상의 숫자여야 합니다.", "INVALID_DURATION"
            )

        duration_ms = min(round(raw_duration), settings.MAX_VIEW_DURATION_MS)

        BoothView.objects.create(
            booth_id=booth_id, visitor_id=visitor_id, duration_ms=duration_ms
        )

        return Response(stat_payload(booth_id), status=201)
