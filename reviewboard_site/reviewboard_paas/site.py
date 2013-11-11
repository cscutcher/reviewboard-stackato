# -*- coding: utf-8 -*-
"""
Management for Paas install reviewboard instance
"""
import json
import logging
import os
import os.path
from random import choice
from reviewboard.cmdline import rbsite
from reviewboard_paas.vcap import VCAPInfo

DEV_LOGGER = logging.getLogger(__name__)


class _Site(object):
    """
    Management for Paas install reviewboard instance
    """
    KEYFILE = "rb_secret.txt"

    def __init__(self):
        self.site_root = "/"
        self.media_rel_url = "media/"
        self.static_rel_url = "static/"

        # Information from env
        self.memcache_url = os.getenv('MEMCACHE_URL')
        self.paas_root = os.getenv('HOME')
        self.debug = (os.getenv('REVIEWBOARD_DEBUG', None) == "True")

        # Information from VCAP
        self.vcap = VCAPInfo()
        self.name = self.vcap.get_name()
        self.domain = self.vcap.get_uris()[0]
        self.site_path = os.path.abspath(self.vcap.get_filesystem_path("%s-site" % (self.name,)))
        self.default_admin_user = os.getenv('REVIEWBOARD_DEFAULT_ADMIN_USER')
        self.default_admin_pass = os.getenv('REVIEWBOARD_DEFAULT_ADMIN_PASS')
        self.default_admin_email = os.getenv('REVIEWBOARD_DEFAULT_ADMIN_EMAIL')
        self.db_type, self.db_info = self.vcap.get_service_by_name("%s-db" % (self.name,))
        self.db_credentials = self.db_info["credentials"]
        self.db_engine = ("django.db.backends.postgresql_psycopg2"
                          if self.db_type == "postgresql" else
                          "django.db.backends.mysql")

        # Other paths
        self.htdocs_path = os.path.join(self.site_path, "htdocs")
        self.media_path = os.path.join(self.htdocs_path, "media")
        self.static_path = os.path.join(self.htdocs_path, "static")
        self.uswgi_config_path = os.path.join(self.paas_root, "uwsgi.json")
        self.installed_flag_path = os.path.join(self.site_path, 'installed')

        # Information from filesystem
        self.secret_key_path = os.path.join(self.site_path, self.KEYFILE)
        self.secret_key = self._get_secret_key()

        self.site = self.rbsite_factory()

    @property
    def installed(self):
        """
        Mark reviewboard as installed
        """
        return os.path.exists(self.installed_flag_path)

    @installed.setter
    def installed(self, value):
        """
        Mark reviewboard as installed
        """
        if value:
            with file(self.installed_flag_path, 'a'):
                        os.utime(self.installed_flag_path, None)
        else:
            try:
                os.remove(self.installed_flag_path)
            except OSError:
                pass

    def _get_secret_key(self):
        try:
            secret_key = file(self.secret_key_path, 'r').read()
        except IOError:
            # Generate a secret key based on Django's code.
            secret_key = ''.join([
                choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
                for i in range(50)
            ])
            file(self.secret_key_path, 'w').write(secret_key)
        return secret_key

    def rbsite_factory(self):
        """
        Create a rbsite.Site instance to help with install and upgrade
        """
        options = type("options", (object,), {})
        options.copy_media = True
        options.upgrade_db = True

        site = rbsite.Site(self.site_path, options)

        site.domain_name = self.domain
        site.web_server_port = "80"
        site.site_root = self.site_root
        site.static_url = self.static_rel_url
        site.media_url = self.media_rel_url
        site.web_server_type = "apache"
        site.python_loader = "wsgi"

        site.admin_user = self.default_admin_user
        site.admin_password = self.default_admin_pass
        site.admin_email = self.default_admin_email

        # Database settings
        site.db_type = self.db_type
        site.db_name = self.db_credentials["name"]
        site.db_host = self.db_credentials["host"]
        site.db_port = self.db_credentials["port"]
        site.db_user = self.db_credentials["user"]
        site.db_pass = self.db_credentials["password"]

        # Cache backend settings.
        site.cache_type = "memcached"
        site.cache_info = self.memcache_url

        rbsite.site = site
        rbsite.options = options
        return site

    def install(self):
        """
        Install new instance of site
        """
        if not self.installed:
            self.site.rebuild_site_directory()
            self.link_settings_local()
            self.setup_settings()
            self.site.sync_database()
            self.site.migrate_database()
            self.site.create_admin_user()
            self.save_initial_settings()
        self.upgrade()
        self.installed = True

    def upgrade(self):
        """
        Upgrade instance
        """
        rbsite.UpgradeCommand().run()

    def manage(self, command, args):
        """
        Manage instance
        """
        self.setup_settings()
        self.site.run_manage_command(command, args)

    def setup_settings(self):
        """
        Setup environmental variables for using django
        """
        os.environ['DJANGO_SETTINGS_MODULE'] = 'reviewboard.settings'
        os.environ['HOME'] = os.path.join(self.site_path, "data")

    def save_initial_settings(self):
        """
        Save initial settings to DB
        """
        from django.contrib.sites.models import Site
        from djblets.siteconfig.models import SiteConfiguration

        cur_site = Site.objects.get_current()
        cur_site.domain = self.site.domain_name
        cur_site.save()

        if self.site.static_url.startswith("http"):
            site_static_url = self.site.static_url
        else:
            site_static_url = self.site.site_root + self.site.static_url

        if self.site.media_url.startswith("http"):
            site_media_url = self.site.media_url
        else:
            site_media_url = self.site.site_root + self.site.media_url

        siteconfig = SiteConfiguration.objects.get_current()
        siteconfig.set("site_static_url", site_static_url)
        siteconfig.set("site_static_root", self.static_path)
        siteconfig.set("site_media_url", site_media_url)
        siteconfig.set("site_media_root", self.media_path)
        siteconfig.set("site_admin_name", self.site.admin_user)
        siteconfig.set("site_admin_email", self.site.admin_email)
        siteconfig.save()

    def link_settings_local(self):
        """
        Add link conf/setting_local.py to settings_local
        """
        os.symlink(os.path.join(self.paas_root, "settings_local.py"),
                   os.path.join(self.site_path, "conf/settings_local.py"))

    def get_application(self):
        """
        Get WSGI application
        """
        self.setup_settings()
        import django.core.handlers.wsgi
        return django.core.handlers.wsgi.WSGIHandler()

    def write_uwsgi_config(self):
        """
        Write uwsgi config
        """
        config = {
            "uwsgi": {
                "wsgi-file": "wsgi.py",
                "static-map2": [
                    "=".join((self.static_rel_url, self.static_path)),
                    "=".join((self.media_rel_url, self.media_path)),
                ]
            }
        }
        json.dump(config, file(self.uswgi_config_path, 'w'))


_site = None


def get_site():
    """
    Get site utility
    """
    global _site
    if _site is None:
        _site = _Site()
    return _site
