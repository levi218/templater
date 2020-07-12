from pyramid.config import Configurator

try:
    # for python 2
    from urlparse import urlparse
except ImportError:
    # for python 3
    from urllib.parse import urlparse

from gridfs import GridFS
from pymongo import MongoClient

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    config =  Configurator(settings=settings)
    db_url = urlparse(settings['mongo_uri'])
    
    config.registry.db = MongoClient(settings['mongo_uri'])

    def add_db(request):
        db = config.registry.db[db_url.path[1:]]
        return db

    def add_fs(request):
        return GridFS(request.db)

    config.add_request_method(add_db, 'db', reify=True)
    config.add_request_method(add_fs, 'fs', reify=True)

    config.include('pyramid_jinja2')
    config.include('.routes')
    config.scan()

    return config.make_wsgi_app()
