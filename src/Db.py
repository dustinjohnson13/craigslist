import sqlite3
from datetime import datetime

from Domain import Item


class Db:
    def __init__(self):
        self.conn = sqlite3.connect('craigslist.db')
        self.cursor = self.conn.cursor()

    def initialize(self):
        # Create tables
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS searches
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT)''')
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS url_idx ON searches (url)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS items
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, link TEXT, version INTEGER, search_id INTEGER)''')
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS link_version_idx ON items (link, version)''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS item_versions
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, title TEXT, date TEXT, description TEXT)''')
        self.cursor.execute('''CREATE UNIQUE INDEX IF NOT EXISTS item_id_idx ON item_versions (item_id)''')

    def close(self):
        self.cursor.close()
        self.conn.close()

    def search_id(self, url):
        self.cursor.execute('SELECT id FROM searches WHERE url=?', (url,))
        search_id = self.cursor.fetchall()

        if not search_id:
            self.cursor.execute("""INSERT INTO searches (url) VALUES (?)""", (url,))
            search_id = self.cursor.lastrowid
        else:
            search_id = search_id[0][0]

        return search_id

    def most_recent_version(self, link):
        self.cursor.execute('SELECT MAX(id) FROM items WHERE link=?', (link,))
        return self.cursor.fetchone()[0]

    def existing_item(self, version_id):
        self.cursor.execute('SELECT i.link, iv.title, iv.description, iv.date ' \
                            'FROM item_versions iv ' \
                            'INNER JOIN items i ON iv.item_id = i.id ' \
                            'WHERE iv.id=?', (version_id,))

        existingVersionRow = self.cursor.fetchall()
        row = existingVersionRow[0]

        # Strip the colon out of the date string
        date_db_string = row[3][:22] + row[3][23:]

        link = row[0]
        title = row[1]
        description = row[2]
        date = datetime.strptime(date_db_string, "%Y-%m-%d %H:%M:%S%z")

        return Item(link, title, description, date)

    def save(self, item, version, search_id):
        try:
            self.cursor.execute("""INSERT INTO items (link, version, search_id) VALUES (?, ?, ?)""",
                                (item.link, version, search_id))

            item_id = self.cursor.lastrowid

            self.cursor.execute("""INSERT INTO item_versions (item_id, title, description, date) VALUES (?, ?, ?, ?)""",
                                (item_id, item.title, item.description, item.date))
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
