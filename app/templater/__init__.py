from pyramid.config import Configurator

import configparser
import io
import os

from gridfs import GridFS
from pymongo import MongoClient

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    config =  Configurator(settings=settings)
    # db_url = urlparse(settings['mongo_uri'])
    
    # config.registry.db = MongoClient(settings['mongo_uri'])

    c = configparser.ConfigParser()
    c.read('config.ini')
    for s in c.sections():
        config.registry.settings[s] = dict(c.items(s))
    if 'DB_PORT_27017_TCP_ADDR' in os.environ:
        config.registry.db = MongoClient(
            os.environ['DB_PORT_27017_TCP_ADDR'],
            27017)
    else:
        try:
            mongo_uri = config.registry.settings['templater']['mongo_uri']
            if mongo_uri is None:
                raise Exception("Database not found")
            else:
                config.registry.db = MongoClient(mongo_uri)
        except:                 
            raise Exception("Database not found")


    def add_db(request):
        db = config.registry.db['templater']
        return db

    def add_fs(request):
        return GridFS(request.db)

    config.add_request_method(add_db, 'db', reify=True)
    config.add_request_method(add_fs, 'fs', reify=True)

    config.include('pyramid_jinja2')
    config.include('.routes')
    config.scan()

    return config.make_wsgi_app()
