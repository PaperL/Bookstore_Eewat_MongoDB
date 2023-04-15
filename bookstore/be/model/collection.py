import pymongo
import database

class Collection():
    def __init__(self, collection_name: str):
        self.database = database.getDatabase()
        self.collection = self.database[collection_name]

    def getCollection(self) -> pymongo.collection.Collection:
        return self.collection