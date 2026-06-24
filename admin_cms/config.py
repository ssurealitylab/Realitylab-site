"""Admin CMS Configuration"""
import os

SITE_ROOT = "/data2/i0179/Realitylab-site"
DATA_DIR = os.path.join(SITE_ROOT, "_data")
SITE_DIR = os.path.join(SITE_ROOT, "_site")
BACKUP_DIR = os.path.join(SITE_ROOT, "admin_cms", "backups")
CONFIG_FILE = os.path.join(SITE_ROOT, "admin_cms", "admin_config.json")

# Image directories
IMAGE_DIRS = {
    "members": os.path.join(SITE_ROOT, "assets", "img", "members"),
    "news": os.path.join(SITE_ROOT, "img", "news"),
    "publications": os.path.join(SITE_ROOT, "assets", "img", "publications"),
    "slider": os.path.join(SITE_ROOT, "참고 이미지", "homepage_slider_images"),
    "timeline": os.path.join(SITE_ROOT, "assets", "img", "timeline"),
}

# Image size limits per category (max_width, max_height, quality)
IMAGE_SIZES = {
    "members": (500, 500, 85),
    "news": (800, 600, 85),
    "publications": (1000, 800, 85),
    "slider": (1920, 1080, 90),
    "timeline": (800, 600, 85),
}

# YAML files that can be edited
EDITABLE_FILES = {
    "members": "members.yml",
    "news": "news.yml",
    "publications": "publications.yml",
    "chatbot_knowledge": "chatbot_knowledge.yml",
    "sitetext": "sitetext.yml",
    "navigation": "navigation.yml",
    "courses": "courses.yml",
    "domestic_publications": "domestic_publications.yml",
}

MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB
MAX_BACKUPS = 50
SESSION_TIMEOUT_HOURS = 4
LOGIN_RATE_LIMIT = 5  # max failed attempts
LOGIN_LOCKOUT_MINUTES = 15

CMS_PORT = 4010
