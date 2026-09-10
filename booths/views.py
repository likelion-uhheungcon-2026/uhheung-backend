import math
from datetime import datetime, timezone

from django.conf import settings
from django.db.models import Avg, Count, IntegerField, Q, Sum, Value
from django.db.models.functions import Cast, Coalesce
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import ApiError
from .models import Booth, BoothView
from .params import parse_enum, parse_enum_list, parse_integer, parse_string
from .serializers import BoothDetailSerializer, BoothSummarySerializer

# 프론트 MenuBox.jsx 의 '이름 순 / 인기 순 / 추천 순' + 지도용 부스 번호 순
SORTS = {
    "id": ["id"],
    "name": ["name", "id"],
    "popular": ["-view_count", "-total_duration_ms", "id"],
    "recommend": ["-recommend_score", "-view_count", "id"],
}

# RecommendedBooth.jsx 의 '최다 조회수' / '최고 조회시간' 카드
RANKING_METRICS = {
    "views": ["-view_count", "-total_duration_ms", "id"],
    "duration": ["-total_duration_ms", "-view_count", "id"],
    "avgDuration": ["-avg_duration_ms", "-view_count", "id"],
}


def with_stats(queryset):
    """부스별 조회 통계를 붙인다. 부스가 40개 수준이라 실시간 집계로 충분하다."""
    return queryset.annotate(
        view_count=Count("views"),
        visitor_count=Count("views__visitor_id", distinct=True),
        total_duration_ms=Coalesce(Sum("views__duration_ms"), Value(0)),
        avg_duration_ms=Cast(
            Coalesce(Avg("views__duration_ms"), Value(0.0)), IntegerField()
        ),
    )


def stat_payload(booth_id):
    """조회 통계만 담은 응답. 프론트가 화면의 조회수를 바로 갱신할 수 있게 한다."""
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
    """GET /api/booths

    프론트 ServiceListPage 의 검색창 + FilterBox + MenuBox 를 한 번에 받는다.
    """

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
        items = with_stats(booths).order_by(*SORTS[sort])[offset : offset + size]

        return Response(
            {
                "items": BoothSummarySerializer(items, many=True).data,
                "page": page,
                "size": size,
                "total": total,
                "totalPages": math.ceil(total / size),
            }
        )


class BoothTagListView(APIView):
    """GET /api/booths/tags — 태그별 부스 수. 필터 칩을 하드코딩하지 않아도 되게 한다."""

    def get(self, request):
        counts = dict(
            Booth.objects.values_list("tag").annotate(count=Count("id")).values_list("tag", "count")
        )

        return Response(
            {"items": [{"tag": tag, "count": counts.get(tag, 0)} for tag in settings.BOOTH_TAGS]}
        )


class BoothRankingView(APIView):
    """GET /api/booths/ranking?metric=views|duration|avgDuration&limit=3"""

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

        return Response({"metric": metric, "items": BoothSummarySerializer(items, many=True).data})


class BoothDetailView(APIView):
    """GET /api/booths/:id — 상세. functions / techStack 배열 포함."""

    def get(self, request, booth_id):
        booth = (
            with_stats(Booth.objects.filter(pk=booth_id))
            .prefetch_related("functions", "tech_stack")
            .first()
        )

        if booth is None:
            raise ApiError.not_found(f"{booth_id}번 부스를 찾을 수 없습니다.", "BOOTH_NOT_FOUND")

        return Response(BoothDetailSerializer(booth).data)


class BoothViewLogView(APIView):
    """부스 조회 로그. '인기 순' 정렬과 랭킹 API 의 원본 데이터."""

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
        if raw_duration < 0 or raw_duration != raw_duration:  # NaN 도 거른다
            raise ApiError.bad_request(
                "durationMs 는 0 이상의 숫자여야 합니다.", "INVALID_DURATION"
            )

        # 상한을 넘는 값은 거절하지 않고 잘라서 기록한다. 통계만 지키면 되고,
        # 이탈 시점 전송은 실패해도 재시도할 방법이 없기 때문.
        duration_ms = min(round(raw_duration), settings.MAX_VIEW_DURATION_MS)

        BoothView.objects.create(
            booth_id=booth_id, visitor_id=visitor_id, duration_ms=duration_ms
        )

        return Response(stat_payload(booth_id), status=201)
