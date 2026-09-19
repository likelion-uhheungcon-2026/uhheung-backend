import io

from django.http import HttpResponse
from PIL import Image


def image_type(data):
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    return "image/png"


def to_jpeg(data):
    with Image.open(io.BytesIO(data)) as image:
        background = Image.new("RGB", image.size, (255, 255, 255))
        rgba = image.convert("RGBA")
        background.paste(rgba, mask=rgba.getchannel("A"))
        buffer = io.BytesIO()
        background.save(buffer, "JPEG", quality=85, optimize=True)
    return buffer.getvalue()


def image_response(request, data):
    data = bytes(data)
    content_type = image_type(data)

    if content_type == "image/webp" and "image/webp" not in request.headers.get("Accept", ""):
        data, content_type = to_jpeg(data), "image/jpeg"

    response = HttpResponse(data, content_type=content_type)
    response["Cache-Control"] = "public, max-age=86400"
    response["Vary"] = "Accept"
    return response
