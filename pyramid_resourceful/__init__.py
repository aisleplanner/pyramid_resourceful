# -*- coding: utf-8 -*-
from resourceful.config import convert_config
from resourceful.publisher import Publisher
import resourceful
import logging
import os
import wsgiref.util
from pyramid.settings import asbool

log = logging.getLogger(__name__)


def resourceful_config(config, prefix='resourceful.'):
    cfg = {'publisher_signature': resourceful.DEFAULT_SIGNATURE}
    for k, v in config.items():
        if k.startswith(prefix):
            cfg[k[len(prefix):]] = v
    return convert_config(cfg)


class Tween(object):
    def __init__(self, handler, config):
        self.use_application_uri = asbool(
            config.pop('resourceful.use_application_uri', False))
        self.config = resourceful_config(config)
        self.handler = handler
        self.publisher = Publisher(resourceful.get_library_registry())
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
    return Tween(handler, registry.settings.copy())


def includeme(config):
    config.add_tween('pyramid_resourceful.tween_factory')


def file_callback(dirname, exts=('.less', '.coffee')):
    """Helper to monitor static resources"""
    for var, script in (('LESSC', 'lessc'),):
        if var not in os.environ:
            for dirname in (os.path.join(os.getcwd(), 'bin'),
                            os.path.expanduser('~/bin'),
                            '/usr/local/bin',
                            '/usr/bin'):
                    binary = os.path.join(dirname, script)
                    if os.path.isfile(binary):
                        os.environ[var] = binary
                        break
        if var not in os.environ:
            print(("Can't find a lessc %s binary" % script))

    def callback():
        resources = []
        for root, dirnames, filenames in os.walk(dirname):
            for filename in filenames:
                dummy, ext = os.path.splitext(filename)
                if ext in exts:
                    resources.append(os.path.join(root, filename))
        return resources
    return callback
