import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 설정 파일 없이 기본값으로 돌아간다. 배포할 때만 환경변수로 덮어쓰면 된다.
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-uhheungcon-local-only")
DEBUG = os.environ.get("DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "booths",
]

MIDDLEWARE = [
    # CorsMiddleware 는 CommonMiddleware 보다 위에 있어야 한다.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / os.environ.get("DB_FILE", "data/uhheung.db"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- REST Framework ---

REST_FRAMEWORK = {
    # 조회 API 는 로그인 없이 열려 있다.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    # 모든 에러를 { "error": { "code", "message" } } 한 가지 모양으로 통일한다.
    "EXCEPTION_HANDLER": "booths.exceptions.api_exception_handler",
    "UNAUTHENTICATED_USER": None,
}

# --- CORS ---
# 쉼표로 여러 개 지정. 배포 시 환경변수로 프론트 주소를 넣는다.
# 5173 이 이미 쓰이고 있으면 vite 가 5174, 5175 로 밀리므로 개발용으로 함께 열어둔다.
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
        ",http://localhost:5174,http://127.0.0.1:5174"
        ",http://localhost:5175,http://127.0.0.1:5175",
    ).split(",")
    if origin.strip()
]

# --- 프로젝트 상수 ---

# 프론트 FilterBox.jsx 의 필터 항목과 반드시 일치해야 한다.
BOOTH_TAGS = ["멋사", "SJF", "AAC", "OPEN"]

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 조회 1건으로 인정할 체류시간 상한(ms). 6시간.
# 탭을 켜둔 채 방치하거나 잘못된 값이 올라와도 통계가 망가지지 않게 자른다.
MAX_VIEW_DURATION_MS = 6 * 60 * 60 * 1000

SEED_FILE = BASE_DIR / "data" / "booths.seed.json"
