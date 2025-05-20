import pymongo
import certifi
from os import environ

client = pymongo.MongoClient(str(environ.get('MONGO_URI')), tlsCAFile=certifi.where())
db = client["milegalista"]