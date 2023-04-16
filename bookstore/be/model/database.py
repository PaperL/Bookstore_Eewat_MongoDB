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

def user_id_exist(user_id) -> bool:
    user_collection = getDatabase()['user']
    # cursor = self.conn.execute("SELECT user_id FROM user WHERE user_id = ?;", (user_id,))
    # row = cursor.fetchone()
    result = user_collection.find ({'user_id': user_id})
    result_list = list (result)
    if len (result_list) == 0:
        return False
    else:
        return True
    
def book_id_exist(store_id, book_id):
    # cursor = self.conn.execute("SELECT book_id FROM store WHERE store_id = ? AND book_id = ?;", (store_id, book_id))
    # row = cursor.fetchone()
    store_collection = getDatabase()['store']
    result = store_collection.find ({'store_id': store_id, 'book_id': book_id})
    result_list = list (result)
    if len (result_list) == 0:
        return False
    else:
        return True

def store_id_exist(store_id):
    # cursor = self.conn.execute("SELECT store_id FROM user_store WHERE store_id = ?;", (store_id,))
    # row = cursor.fetchone()
    user_store_collection = getDatabase()['user_store']
    result = user_store_collection.find ({'store_id': store_id})
    result_list = list (result)
    if len (result_list) == 0:
        return False
    else:
        return True