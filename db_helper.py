def file_found(name, date_created, db_cursor):
    db_cursor.execute("SELECT EXISTS(SELECT 1 FROM files WHERE file_name = ? AND date_created = ?)", (name, date_created,))
    data = db_cursor.fetchall()
    if not data[0][0] == 0:
        return True
    else:
        return False
