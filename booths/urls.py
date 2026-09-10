from django.urls import path

from .views import (
    BoothDetailView,
    BoothListView,
    BoothRankingView,
    BoothTagListView,
    BoothViewLogView,
)

urlpatterns = [
    path("booths", BoothListView.as_view()),
    # /booths/<id> 보다 먼저 선언해야 tags, ranking 이 id 로 잡히지 않는다.
    path("booths/tags", BoothTagListView.as_view()),
    path("booths/ranking", BoothRankingView.as_view()),
    path("booths/<int:booth_id>", BoothDetailView.as_view()),
    path("booths/<int:booth_id>/views", BoothViewLogView.as_view()),
]
