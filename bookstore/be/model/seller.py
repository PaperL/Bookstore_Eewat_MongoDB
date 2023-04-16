# import sqlite3 as sqlite
from typing import Tuple
import pymongo
import pymongo.errors
from be.model import error
# from be.model import db_conn
from be.model.collection import Collection
from be.model.database import user_id_exist, book_id_exist, store_id_exist

class Seller():

    def __init__(self):
        # db_conn.DBConn.__init__(self)
        self.storeCollection = Collection("store").collection
        self.storeCollection.create_index([("store_id", 1), ("book_id", 1)], unique=True)
        self.userStoreCollection = Collection ("user_store").collection
        self.userStoreCollection.create_index ([("user_id", 1), ("store_id", 1)], unique=True)

    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            # self.conn.execute("INSERT into store(store_id, book_id, book_info, stock_level)"
            #                   "VALUES (?, ?, ?, ?)", (store_id, book_id, book_json_str, stock_level))
            # self.conn.commit()

            self.storeCollection.insert_one (
                {
                    "store_id": store_id, 
                    "book_id": book_id, 
                    "book_info": book_json_str, 
                    "stock_level": stock_level
                }
            )
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # self.conn.execute("UPDATE store SET stock_level = stock_level + ? "
            #                   "WHERE store_id = ? AND book_id = ?", (add_stock_level, store_id, book_id))
            # self.conn.commit()
            update_result = self.storeCollection.update_one (
                {"store_id": store_id, "book_id": book_id},
                {"$inc": {"stock_level": add_stock_level}}
            )
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> Tuple[int, str]:
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            # self.conn.execute("INSERT into user_store(store_id, user_id)"
            #                   "VALUES (?, ?)", (store_id, user_id))
            # self.conn.commit()
            self.userStoreCollection.insert_one (
                {
                    "store_id": store_id, 
                    "user_id": user_id
                }
            )
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
