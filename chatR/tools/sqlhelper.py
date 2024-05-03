from dbutils.pooled_db import PooledDB
import pymysql

from chatR.config.config import config


class SqlHelper(object):
    def __init__(self):
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=config.max_connections,
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            charset=config.charset,
            mincached=config.min_cached
        )

    def open(self):
        conn = self.pool.connection()
        cursor = conn.cursor()
        return conn, cursor

    def close(self, conn, cursor):
        conn.close()
        cursor.close()

    def fetchall(self, sql, *args):
        conn, cursor = self.open()
        cursor.execute(sql, args)
        result = cursor.fetchall()
        self.close(conn, cursor)
        return result

    def fetchone(self, sql, *args):
        conn, cursor = self.open()
        cursor.execute(sql, args)
        result = cursor.fetchone()
        self.close(conn, cursor)
        return result

    def addone(self, sql, *args):
        try:
            conn, cursor = self.open()
            cursor.execute(sql, args)
            conn.commit()
            self.close(conn, cursor)
            return True
        except Exception as e:
            print(f"数据库出错: {e}")
            return False

    def add_item(self, sql, *args):
        try:
            conn, cursor = self.open()
            cursor.execute(sql, args)
            conn.commit()
            last_row_id = cursor.lastrowid
            cursor.execute("SELECT * FROM item WHERE i_id = %s", last_row_id)
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(f"添加item: {e}")
            return None
        finally:
            self.close(conn, cursor)

    def add_public_item(self, sql, *args):
        try:
            conn, cursor = self.open()
            cursor.execute(sql, args)
            conn.commit()
            last_row_id = cursor.lastrowid
            cursor.execute("SELECT * FROM public_item WHERE pi_id = %s", last_row_id)
            result = cursor.fetchone()
            return result
        except Exception as e:
            print(f"添加item: {e}")
            return None
        finally:
            self.close(conn, cursor)

    def add_chat(self, sql, *args):
        try:
            conn, cursor = self.open()
            cursor.execute(sql, args)
            conn.commit()
            last_row_id = cursor.lastrowid
            return last_row_id
        except Exception as e:
            print(f"添加chat: {e}")
            return None
        finally:
            self.close(conn, cursor)

    def add_file(self, sql, *args):
        try:
            conn, cursor = self.open()
            cursor.execute(sql, args)
            conn.commit()
            last_row_id = cursor.lastrowid
            return last_row_id
        except Exception as e:
            print(f"添加file: {e}")
            return None
        finally:
            self.close(conn, cursor)

    def update(self, sql, *args):
        try:
            conn, cursor = self.open()
            cursor.execute(sql, args)
            conn.commit()
            self.close(conn, cursor)
            return True
        except Exception as e:
            print(f"数据库出错: {e}")
            return False


db = SqlHelper()
