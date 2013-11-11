# -*- coding: utf-8 -*-
"""
Access to VCAP information in environment
"""
import json
import logging
import os

DEV_LOGGER = logging.getLogger(__name__)


class VCAPInfo(object):
    """
    Convenience class to get information about PaaS host
    """
    def __init__(self):
        self.application_info = json.loads(os.environ['VCAP_APPLICATION'])
        self.service_info = json.loads(os.environ['VCAP_SERVICES'])

    def get_name(self):
        """
        Get application name
        """
        return self.application_info["name"]

    def get_services(self, service_name):
        """
        Get service by service type
        """
        return self.service_info.get(service_name, [])

    def get_service_by_name(self, name, default=None):
        """
        Get service by name
        """
        for service_type, services in self.service_info.items():
            for service in services:
                if service["name"] == name:
                    return service_type, service
        return default

    def get_filesystem_path(self, name):
        for filesystem_info in self.service_info["filesystem"]:
            if filesystem_info["name"] == name:
                return filesystem_info["dir"]
        raise KeyError("Unable to find %s" % (name,))

    def get_uris(self):
        return self.application_info["uris"]
