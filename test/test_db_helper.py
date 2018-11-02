import os
import sqlite3
import unittest
import db_helper


class TestDbHelper(unittest.TestCase):
    
    def setUp(self):
        # create db file
        db_name = "test_db.sqlite"
        db_conn = None
        db_cursor = None

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
        db_name = "test_db.sqlite"

        # remove db_file
        os.remove(db_name)

    def test_file_found(self):
        db_cursor = None

        file = "test_file"
        date_created = "2018-08-10"

        self.assertFalse(db_helper.file_found(file, date_created, db_cursor))
