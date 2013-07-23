# -*- coding: utf-8 -*-
from resourceful.config import convert_config
from resourceful.publisher import Publisher
from resourceful.registry import Registry
from zope.interface import Interface
import resourceful
import logging
import os
import wsgiref.util
from pyramid.settings import asbool

log = logging.getLogger(__name__)


class IFanstaticRegistry(Interface):
    pass


def resourceful_config(config, prefix='resourceful.'):
    cfg = {'publisher_signature': resourceful.DEFAULT_SIGNATURE}
    for k, v in config.items():
        if k.startswith(prefix):
            cfg[k[len(prefix):]] = v
    return convert_config(cfg)


class Tween(object):
    def __init__(self, handler, registry):
        config = registry.settings.copy()
        self.use_application_uri = asbool(
            config.pop('resourceful.use_application_uri', False))
        self.config = resourceful_config(config)
        self.handler = handler
        resourceful_registry = registry.queryUtility(IFanstaticRegistry)
        self.publisher = Publisher(resourceful_registry)
        self.publisher_signature = self.config.get('publisher_signature')
        self.trigger = '/%s/' % self.publisher_signature

    def __call__(self, request):

        # publisher
        if len(request.path_info.split(self.trigger)) > 1:
            path_info = request.path_info
            ignored = request.path_info_pop()
            while ignored != self.publisher_signature:
                ignored = request.path_info_pop()
            response = request.get_response(self.publisher)
            # forward to handler if the resource could not be found
            if response.status_int == 404:
                request.path_info = path_info
                return self.handler(request)
            return response

        # injector
        needed = resourceful.init_needed(**self.config)
        if self.use_application_uri and not needed.has_base_url():
            base_url = wsgiref.util.application_uri(request.environ)
            # remove trailing slash for resourceful
            needed.set_base_url(base_url.rstrip('/'))
        request.environ[resourceful.NEEDED] = needed

        response = self.handler(request)

        if not (response.content_type and
                response.content_type.lower() in ['text/html',
                                                  'text/xml']):
            resourceful.del_needed()
            return response

        if needed.has_resources():
            result = needed.render_topbottom_into_html(response.body)
            response.body = ''
            response.write(result)
        resourceful.del_needed()
        return response


def tween_factory(handler, registry):
    return Tween(handler, registry)


def add_library(config, library):
    def callback():
        resourceful_registry = config.registry.queryUtility(IFanstaticRegistry)
        resourceful_registry.add(library)
    discriminator = ('add_library', library.name)
    config.action(discriminator, callable=callback)


def includeme(config):
    resourceful_registry = Registry()
    config.registry.registerUtility(resourceful_registry, IFanstaticRegistry)

    config.add_tween('pyramid_resourceful.tween_factory')
    config.add_directive('add_library', add_library)
