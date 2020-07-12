import os
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from paste.deploy import loadapp
from waitress import serve
from gridfs import GridFS
from pymongo import MongoClient
import datetime
try:
    # for python 2
    from urlparse import urlparse
except ImportError:
    # for python 3
    from urllib.parse import urlparse

mongo_uri = 'mongodb+srv://levi218:K5Qa2f8HsGO8Uffl@cluster0.uoxsf.mongodb.net/templater?retryWrites=true&w=majority'
db_url = urlparse(mongo_uri)

def remove_old_files():
    print("background task running...")
    db = MongoClient(mongo_uri)[db_url.path[1:]]
    fs = GridFS(db)
    count = 0
    delta = datetime.timedelta(hours=-1, minutes=0, seconds=0)
    for gridout in fs.find({'uploadDate': {'$lt' : datetime.datetime.utcnow() + delta }}):
        fs.delete(gridout._id)
        count+=1
    print("removed: "+str(count))


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(remove_old_files,
        trigger='interval', 
        id='Remove old files', 
        minutes=1
    )

    atexit.register(lambda: scheduler.shutdown())

    port = int(os.environ.get("PORT", 5000))
    app = loadapp('config:development.ini', relative_to='.')

    serve(app, host='0.0.0.0', port=port)
    
