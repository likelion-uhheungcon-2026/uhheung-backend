from django.http import Http404, JsonResponse
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler


class ApiError(APIException):
    """뷰에서 던지면 그대로 상태코드와 메시지가 되는 에러."""

    def __init__(self, status_code, code, message):
        self.status_code = status_code
        self.code = code
        self.detail = message

    @classmethod
    def bad_request(cls, message, code="BAD_REQUEST"):
        return cls(400, code, message)

    @classmethod
    def not_found(cls, message, code="NOT_FOUND"):
        return cls(404, code, message)


def _body(code, message):
    return {"error": {"code": code, "message": message}}


def api_exception_handler(exc, context):
    """DRF 의 모든 에러 응답을 { "error": { "code", "message" } } 로 통일한다."""
    if isinstance(exc, ApiError):
        response = drf_exception_handler(exc, context)
        response.data = _body(exc.code, str(exc.detail))
        return response

    if isinstance(exc, Http404):
        response = drf_exception_handler(exc, context)
        response.data = _body("NOT_FOUND", "요청한 리소스를 찾을 수 없습니다.")
        return response

    response = drf_exception_handler(exc, context)
    if response is None:
        # DRF 가 처리하지 못한 예외는 그대로 올려보내 Django 가 500 을 내게 한다.
        return None

    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    response.data = _body(
        getattr(exc, "default_code", "ERROR").upper(),
        str(detail) if detail else "요청을 처리할 수 없습니다.",
    )
    return response


def not_found(request, exception=None):
    return JsonResponse(
        _body("NOT_FOUND", f"{request.method} {request.path} 는 없는 경로입니다."),
        status=404,
    )


def server_error(request):
    return JsonResponse(_body("INTERNAL_ERROR", "서버 내부 오류가 발생했습니다."), status=500)
