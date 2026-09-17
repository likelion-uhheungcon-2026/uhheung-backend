from django.urls import path

from .views import (
    BoothDetailView,
    BoothImageView,
    BoothListView,
    BoothLogoView,
    BoothRankingView,
    BoothTagListView,
    BoothViewLogView,
)

urlpatterns = [
    path("booths", BoothListView.as_view()),
    path("booths/tags", BoothTagListView.as_view()),
    path("booths/ranking", BoothRankingView.as_view()),
    path("booths/<int:booth_id>", BoothDetailView.as_view()),
    path("booths/<int:booth_id>/image", BoothImageView.as_view()),
    path("booths/<int:booth_id>/logo", BoothLogoView.as_view()),
    path("booths/<int:booth_id>/views", BoothViewLogView.as_view()),
]
