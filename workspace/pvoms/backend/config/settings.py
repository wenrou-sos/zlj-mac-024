"""
光伏电站运维系统 (PVOMS) Django 配置

数据库默认使用 SQLite 便于本地快速演示；
生产环境设置环境变量 DATABASE_URL=postgres://user:pass@host:5432/pvoms
即可切换到 PostgreSQL（无需修改代码）。
"""
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent          # backend/
# 前端构建产物目录，可用环境变量覆盖（默认仓库布局 backend/ 与 frontend/ 同级）
FRONTEND_DIST = Path(os.environ.get(
    "FRONTEND_DIST", BASE_DIR.parent / "frontend" / "dist"))

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "pvoms-dev-secret-key-change-in-prod")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "core",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIST],
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

# 数据库：默认 SQLite，DATABASE_URL 存在时使用 PostgreSQL
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# 前端构建产物 (vite build -> frontend/dist, base=/static/)
STATIC_URL = "/static/"
STATICFILES_DIRS = [FRONTEND_DIST] if FRONTEND_DIST.exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# 开发期允许 vite dev server 跨域；生产由 Django 直接托管前端，无跨域问题
CORS_ALLOW_ALL_ORIGINS = DEBUG

REST_FRAMEWORK = {
    "DATETIME_FORMAT": "%Y-%m-%d %H:%M",
    "DATE_FORMAT": "%Y-%m-%d",
}
