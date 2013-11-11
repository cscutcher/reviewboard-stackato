"""
WSGI app for reviewboard
"""
from reviewboard_paas.site import get_site
application = get_site().get_application()
