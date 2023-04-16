import sqlite3 as sqlite
import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from be.model.collection import Collection
from be.model.database import user_id_exist, book_id_exist, store_id_exist
import pymongo
import pymongo.errors

class Buyer():
    def __init__(self):
        # db_conn.DBConn.__init__(self)
        self.userCollection = Collection("user").collection
        self.userCollection.create_index([("user_id", 1)], unique = True)
        self.storeCollection = Collection("store").collection
        self.storeCollection.create_index([("store_id", 1), ("book_id", 1)], unique = True)
        self.userstoreCollection = Collection("user_store").collection
        self.userstoreCollection.create_index([("user_id", 1), ("store_id", 1)], unique = True)
        self.neworderCollection = Collection("new_order").collection
        self.neworderCollection.create_index([("order_id", 1)], unique = True)
        self.neworderdetailCollection = Collection("new_order_detail").collection
        self.neworderdetailCollection.create_index([("order_id", 1), ("book_id", 1)], unique = True)

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id, )
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id, )
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            for book_id, count in id_and_count:
                # cursor = self.conn.execute(
                #     "SELECT book_id, stock_level, book_info FROM store "
                #     "WHERE store_id = ? AND book_id = ?;",
                #     (store_id, book_id))
                # row = cursor.fetchone()
                row = list(self.storeCollection.find({"store_id": store_id, "book_id": book_id}, {"_id": 0, "book_id": 1, "stock_level": 1, "book_info": 1}))
                if row is None:
                    return error.error_non_exist_book_id(book_id) + (order_id, )

                stock_level = row[0]['stock_level']
                book_info = row[0]['book_info']
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                # cursor = self.conn.execute(
                #     "UPDATE store set stock_level = stock_level - ? "
                #     "WHERE store_id = ? and book_id = ? and stock_level >= ?; ",
                #     (count, store_id, book_id, count))
                cursor = self.storeCollection.update_many(
                    {"store_id": store_id, "book_id": book_id, "stock_level": {"$gte": count}},
                    {"$dec": {"stock_level": count}}
                )
                if len(list(cursor)) == 0:
                    return error.error_stock_level_low(book_id) + (order_id, )

                # self.conn.execute(
                #         "INSERT INTO new_order_detail(order_id, book_id, count, price) "
                #         "VALUES(?, ?, ?, ?);",
                #         (uid, book_id, count, price))
                result = self.neworderdetailCollection.insert_one({"order_id": uid, "book_id": book_id, "count": count, "price": price})

            # self.conn.execute(
            #     "INSERT INTO new_order(order_id, store_id, user_id) "
            #     "VALUES(?, ?, ?);",
            #     (uid, store_id, user_id))
            # self.conn.commit()
            result = self.neworderCollection.insert_one({"order_id": uid, "store_id": store_id, "user_id": user_id})
            order_id = uid
        except pymongo.errors.PyMongoError as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        # conn = self.conn
        try:
            # cursor = conn.execute("SELECT order_id, user_id, store_id FROM new_order WHERE order_id = ?", (order_id,))
            # row = cursor.fetchone()
            row = list(self.neworderCollection.find({"order_id": order_id}, {"_id": 0, "order_id": 1, "user_id" : 1, "store_id": 1}))
            if row is None:
                return error.error_invalid_order_id(order_id)

            order_id = row[0]['order_id']
            buyer_id = row[0]['user_id']
            store_id = row[0]['store_id']

            if buyer_id != user_id:
                return error.error_authorization_fail()

            # cursor = conn.execute("SELECT balance, password FROM user WHERE user_id = ?;", (buyer_id,))
            # row = cursor.fetchone()
            row = list(self.userCollection.find({"user_id": buyer_id}, {"_id": 0, "balance": 1, "password": 1}))
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = row[0]['balance']
            if password != row[0]['password']:
                return error.error_authorization_fail()

            # cursor = conn.execute("SELECT store_id, user_id FROM user_store WHERE store_id = ?;", (store_id,))
            # row = cursor.fetchone()
            row = list(self.userstoreCollection.find({"store_id": store_id}, {"_id": 0, "store_id": 1, "user_id": 1}))
            if row is None:
                return error.error_non_exist_store_id(store_id)

            seller_id = row[0]['user_id']

            if not user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            # cursor = conn.execute("SELECT book_id, count, price FROM new_order_detail WHERE order_id = ?;", (order_id,))
            cursor = self.neworderdetailCollection.find({"order_id": order_id}, {"_id": 0, "book_id": 1, "count": 1, "price": 1})
            total_price = 0
            for row in cursor:
                count = row[0]['count']
                price = row[0]['price']
                total_price = total_price + price * count

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            # cursor = conn.execute("UPDATE user set balance = balance - ?"
            #                       "WHERE user_id = ? AND balance >= ?",
            #                       (total_price, buyer_id, total_price))
            cursor = self.userCollection.update_one(
                {"user_id": buyer_id, "balance": {"$gte": total_price}},
                {"$dnc": {"balance": total_price}}
            )
            if len(list(cursor)) == 0:
                return error.error_not_sufficient_funds(order_id)

            # cursor = conn.execute("UPDATE user set balance = balance + ?"
            #                       "WHERE user_id = ?",
            #                       (total_price, buyer_id))
            cursor = self.userCollection.update_one(
                {"user_id": buyer_id},
                {"$inc": {"balance": total_price}}
            )
            if len(list(cursor)) == 0:
                return error.error_non_exist_user_id(buyer_id)

            # cursor = conn.execute("DELETE FROM new_order WHERE order_id = ?", (order_id, ))
            cursor = self.neworderCollection.delete_one({"order_id": order_id})
            if len(list(cursor)) == 0:
                return error.error_invalid_order_id(order_id)

            # cursor = conn.execute("DELETE FROM new_order_detail where order_id = ?", (order_id, ))
            cursor = self.neworderdetailCollection.delete_one({"order_id": order_id})
            if len(list(cursor)) == 0:
                return error.error_invalid_order_id(order_id)

            # conn.commit()

        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            # cursor = self.conn.execute("SELECT password  from user where user_id=?", (user_id,))
            # row = cursor.fetchone()
            row = list(self.userCollection.find({"user_id": user_id}, {"_id": 0, "password": 1}))
            if row is None:
                return error.error_authorization_fail()

            if row[0]['password'] != password:
                return error.error_authorization_fail()

            # cursor = self.conn.execute(
            #     "UPDATE user SET balance = balance + ? WHERE user_id = ?",
            #     (add_value, user_id))
            cursor = self.userCollection.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": add_value}}
            )
            if len(list(cursor)):
                return error.error_non_exist_user_id(user_id)

            # self.conn.commit()
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"
