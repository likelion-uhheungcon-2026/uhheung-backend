from django.urls import include, path, re_path

from booths.exceptions import not_found
from booths.views import health

urlpatterns = [
    path("api/health", health),
    path("api/", include("booths.urls")),
    re_path(r"^.*$", not_found),
]

handler404 = "booths.exceptions.not_found"
handler500 = "booths.exceptions.server_error"
