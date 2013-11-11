"""
Config for reviewboard
"""
from reviewboard_paas.site import get_site

site = get_site()

LOCAL_ROOT = site.site_path

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": site.db_engine,
        "NAME": site.db_credentials["name"],
        "USER": site.db_credentials["user"],
        "PASSWORD": site.db_credentials["password"],
        "HOST": site.db_credentials["host"],
        "PORT": site.db_credentials["port"],
    }
}

SECRET_KEY = site.secret_key

# Cache backend settings.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': site.memcache_url,
    },
}

# Extra site information.
SITE_ID = 1
SITE_ROOT = site.site_root
FORCE_SCRIPT_NAME = ''
DEBUG = site.debug
