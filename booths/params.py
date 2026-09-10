
from .exceptions import ApiError


def parse_string(value, field, max_length=100):
    if value is None:
        return ""

    trimmed = value.strip()
    if len(trimmed) > max_length:
        raise ApiError.bad_request(f"{field} 는 {max_length}자를 넘을 수 없습니다.")
    return trimmed


def parse_integer(value, field, minimum, maximum, fallback):
    if value is None or value == "":
        return fallback

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ApiError.bad_request(f"{field} 는 정수여야 합니다.") from None

    if parsed < minimum or parsed > maximum:
        raise ApiError.bad_request(f"{field} 는 {minimum} 이상 {maximum} 이하여야 합니다.")
    return parsed


def parse_enum(value, field, allowed, fallback):
    if value is None or value == "":
        return fallback

    if value not in allowed:
        raise ApiError.bad_request(f"{field} 는 {', '.join(allowed)} 중 하나여야 합니다.")
    return value


def parse_enum_list(value, field, allowed):
    if not value:
        return []

    items = []
    for raw in value.split(","):
        item = raw.strip()
        if item and item not in items:
            items.append(item)

    unknown = [item for item in items if item not in allowed]
    if unknown:
        raise ApiError.bad_request(
            f"{field} 에 알 수 없는 값이 있습니다: {', '.join(unknown)}"
            f" (가능한 값: {', '.join(allowed)})"
        )
    return items
