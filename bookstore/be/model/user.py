import jwt
import time
import logging
# import sqlite3 as sqlite
import pymongo
from be.model import error
# from be.model import db_conn
# from be.model import database
from be.model.collection import Collection

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }


def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded.encode("utf-8").decode("utf-8")


# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(Collection):
    token_lifetime: int = 3600  # 3600 second

    def __init__(self):
        # db_conn.DBConn.__init__(self)
        Collection.__init__(self, "user")

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False

    def register(self, user_id: str, password: str):
        try:
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            # self.conn.execute(
            #     "INSERT into user(user_id, password, balance, token, terminal) "
            #     "VALUES (?, ?, ?, ?, ?);",
            #     (user_id, password, 0, token, terminal), )
            # self.conn.commit()
            
            # mongoDB example
            self.collection.insert_one(
                {
                    "user_id": user_id,
                    "password": password,
                    "balance": 0,
                    "token": token,
                    "terminal": terminal
                }
            )
        except pymongo.errors.DuplicateKeyError as e:
            return error.error_exist_user_id(user_id)
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> tuple(int, str):
        # cursor = self.conn.execute("SELECT token from user where user_id=?", (user_id,))
        # row = cursor.fetchone()
        result_dict = self.collection.find ({'user_id': user_id})
        if len (result_dict) == 0:
            return error.error_authorization_fail()
        db_token = result_dict[0]['token']
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> tuple(int, str):
        # cursor = self.conn.execute("SELECT password from user where user_id=?", (user_id,))
        # row = cursor.fetchone()
        result_dict = self.collection.find ({'usre_id': user_id})
        if len (result_dict) is None:
            return error.error_authorization_fail()

        if password != result_dict[0]['password']:
            return error.error_authorization_fail()

        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> tuple(int, str, str):
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            # cursor = self.conn.execute(
            #     "UPDATE user set token= ? , terminal = ? where user_id = ?",
            #     (token, terminal, user_id), )
            update_result = self.collection.updateOne (
                {"user_id": user_id},
                {"$set": {"token": token, "terminal": terminal}}
            )
            if update_result["matchedCount"] == 0:
                return error.error_authorization_fail() + ("", )
        except pymongo.errors as e:
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            # cursor = self.conn.execute(
            #     "UPDATE user SET token = ?, terminal = ? WHERE user_id=?",
            #     (dummy_token, terminal, user_id), )
            update_result = self.collection.updateOne (
                {"user_id": user_id},
                {"$set": {"token": dummy_token, "terminal": terminal}}
            )
            if update_result["matchedCount"] == 0:
                return error.error_authorization_fail()
        except pymongo.errors as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> tuple(int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message

            # cursor = self.conn.execute("DELETE from user where user_id=?", (user_id,))
            delete_result = self.collection.deleteOne({"user_id": user_id})
            if delete_result['deletedCount'] == 0:
                return error.error_authorization_fail()
        except pymongo.errors as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            # cursor = self.conn.execute(
            #     "UPDATE user set password = ?, token= ? , terminal = ? where user_id = ?",
            #     (new_password, token, terminal, user_id), )
            update_result = self.collection.updateOne (
                {"user_id": user_id},
                {"$set": {"password": new_password, "token": token, "terminal": terminal}}
            )
            if update_result["matchedCount"] == 0:
                return error.error_authorization_fail()
            
        except pymongo.errors as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

