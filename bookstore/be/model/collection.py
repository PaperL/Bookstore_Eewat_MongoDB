import pymongo
from be.model import database

class Collection():
    def __init__(self, collection_name: str):
        self.database: pymongo.database.Database = database.getDatabase()
        self.collection: pymongo.collection.Collection = self.database[collection_name]

    def getCollection(self) -> pymongo.collection.Collection:
        return self.collection