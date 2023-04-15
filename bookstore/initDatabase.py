import sqlite3
import pymongo
conn = sqlite3.connect('fe/data/book.db')
cur = conn.cursor()
cur.execute("SELECT * FROM book")
rows = cur.fetchall()
cur.close()
conn.close()

client = pymongo.MongoClient ('localhost', 27017)
client.drop_database("bookstore")
db = client['bookstore']
books = db['book']

for row in rows:
    book = {
        'id': row[0],
        'title': row[1],
        'author': row[2],
        'publisher': row[3],
        'original_title': row[4],
        'translator': row[5],
        'pub_year': row[6],
        'pages': row[7],
        'price': row[8],
        'currency_unit': row[9],
        'binding': row[10],
        'isbn': row[11],
        'author_intro': row[12],
        'book_intro': row[13],
        'content': row[14],
        'tags': row[15],
        'picture': row[16]
    }
    books.insert_one(book)

client.close()