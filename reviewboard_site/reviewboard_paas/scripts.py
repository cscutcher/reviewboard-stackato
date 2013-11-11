# -*- coding: utf-8 -*-
"""
Command line scripts
"""
import logging
import sys
from reviewboard_paas.site import get_site

DEV_LOGGER = logging.getLogger(__name__)


def install():
    """
    Install PaaS reviewboard site
    """
    get_site().install()


def create_uwsgi_config():
    """
    Create config for uswgi
    """
    get_site().write_uwsgi_config()


def rb_site_upgrade():
    """
    Run upgrade rb_site upgrade
    """
    get_site().upgrade()


def rb_site_manage():
    """
    Run manage command on site
    """
    get_site().manage(sys.argv[1], sys.argv[2:])
