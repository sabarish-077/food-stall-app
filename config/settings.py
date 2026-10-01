"""Development settings for the Restaurant App starter."""
from pathlib import Path
import importlib.util
import os

BASE_DIR = Path(__file__).resolve().parent.parent
# Load private local settings from .env without adding a new package dependency.
env_file = BASE_DIR / ".env"
if env_file.is_file():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", os.getenv("SECRET_KEY", "dev-only-change-before-deploying"))
on_vercel = bool(os.getenv("VERCEL") or os.getenv("VERCEL_URL") or os.getenv("VERCEL_PROJECT_PRODUCTION_URL"))
DEBUG = os.getenv("DEBUG", "false" if on_vercel else "true").strip().lower() in {"1", "true", "yes", "on"}
allowed_hosts = [host.strip() for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",") if host.strip()]
if on_vercel:
    # Include Vercel deployment hosts even if an old ALLOWED_HOSTS value remains configured.
    allowed_hosts.extend([".vercel.app", os.getenv("VERCEL_URL", ""), os.getenv("VERCEL_PROJECT_PRODUCTION_URL", "")])
ALLOWED_HOSTS = list(dict.fromkeys(host for host in allowed_hosts if host))
csrf_origins = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin.strip()]
if os.getenv("VERCEL_URL"):
    csrf_origins.append(f"https://{os.environ['VERCEL_URL']}")
CSRF_TRUSTED_ORIGINS = csrf_origins
if not DEBUG and SECRET_KEY == "dev-only-change-before-deploying":
    raise ValueError("Set a private SECRET_KEY environment variable before running with DEBUG=false.")

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "corsheaders", "restaurants",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
# Use WhiteNoise for production static files when the deployment requirements are installed.
if importlib.util.find_spec("whitenoise"):
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    # Search the custom templates before Django's built-in admin templates.
    "DIRS": [BASE_DIR / "restaurants" / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug", "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"

# SQLite remains the local default; hosted PostgreSQL is configured with DATABASE_URL.
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()
DATABASE_URL = (    os.getenv("DATABASE_URL")    or os.getenv("POSTGRES_URL")    or os.getenv("DATABASE_URL_UNPOOLED")    or os.getenv("POSTGRES_URL_NON_POOLING")    or "").strip()
if DATABASE_URL:
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(
        DATABASE_URL, conn_max_age=0, ssl_require=not DEBUG,
    )}
elif DB_ENGINE == "mysql":
    import MySQLdb  # Provided by mysqlclient when MySQL is selected.
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("DB_NAME", "foodstall_db"),
        "USER": os.getenv("DB_USER", "foodstall_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        "PORT": os.getenv("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
        "CONN_MAX_AGE": 60,
    }}
elif DB_ENGINE == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    raise ValueError("Set DATABASE_URL for PostgreSQL, or DB_ENGINE to 'sqlite' or 'mysql'.")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STALL_NAME = "Food Stall"  # Replace this when you choose the stall's name.
DELIVERY_FEE = 40
STALL_PHONE = ""
STALL_WHATSAPP = ""
STALL_ADDRESS = "Add your stall address in config/settings.py"
STALL_HOURS = "Open daily · 10:00 AM – 10:00 PM"
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:5000", "http://localhost:5001"]
REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"]}
