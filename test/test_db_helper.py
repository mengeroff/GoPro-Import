import os
import sqlite3
import unittest
import db_helper


class TestDbHelper(unittest.TestCase):
    db_name = "test_db.sqlite"
    db_conn = None
    db_cursor = None

    def setUp(self):
        global db_name
        global db_conn
        global db_cursor

        # create db file

        open(db_name, 'a').close()
        db_conn = sqlite3.connect(db_name)
        db_cursor = db_conn.cursor()

        # Create table
        db_cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS files (file_name text, date_created text, date_copied text, size real)
            """
        )

    def tearDown(self):
        global db_name
        global db_cursor
        global db_conn

        # remove db_file
        os.remove(db_name)

    def test_file_found(self):
        global db_cursor
        global db_conn

        file = "test_file"
        date_created = "2018-08-10"

        self.assertFalse(db_helper.file_found(file, date_created, db_cursor))
