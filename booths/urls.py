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

def route(pattern, view):
    return [path(pattern, view), path(f"{pattern}/", view)]


urlpatterns = [
    *route("booths", BoothListView.as_view()),
    *route("booths/tags", BoothTagListView.as_view()),
    *route("booths/ranking", BoothRankingView.as_view()),
    *route("booths/<int:booth_id>", BoothDetailView.as_view()),
    *route("booths/<int:booth_id>/image", BoothImageView.as_view()),
    *route("booths/<int:booth_id>/logo", BoothLogoView.as_view()),
    *route("booths/<int:booth_id>/views", BoothViewLogView.as_view()),
]
