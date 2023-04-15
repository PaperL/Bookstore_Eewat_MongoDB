import pymongo

class Database:
    def __init__ (self):
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.database = self.client["bookstore"]
    
    def getDatabaseClient(self) -> pymongo.MongoClient:
        return self.client

    def getDatabase(self) -> pymongo.database.Database:
        return self.database

database_instance: Database = None

def init_database():
    global database_instance
    database_instance = Database()

def getDatabase () -> pymongo.database.Database:
    global database_instance
    return database_instance.getDatabase()