import pymysql
import yaml
import random
import time
from datetime import datetime

class App:
    """
    mock app to insert data to mysql.
    To test the main app we must provide a way to insert data
    to mysql and have rotated logs.
    In development stage file logs can contain 100Kb only, after that it rotates.

    This app connect to rds and insert random data to hotmart.sales table
    """

    list_users = ["UserA", "UserB", "UserC"]
    time_wait = 0.05

    def __init__(self, host, port, user, password, db, table):
        self.query_insert = """insert into sales (id, ts_sale, name) 
        values (uuid(), now(), '{}')"""
        self.connection = pymysql.connect(host=host,
                                    user=user,
                                    password=password,
                                    db=db,
                                    charset="utf8mb4",
                                    cursorclass=pymysql.cursors.DictCursor)

    def __call__(self):
        try:
            while 1:
                sql = self.query_insert.format(
                    random.choice(self.list_users))
                with self.connection.cursor() as cursor:
                    cursor.execute(sql)
                self.connection.commit()
                print(datetime.now(), sql)
                time.sleep(self.time_wait)     
        finally:
            print('\nconnection closed')
            self.connection.close()

if __name__ == "__main__":
    stream = open("config.yaml", "r")
    config = yaml.load(stream, Loader=yaml.FullLoader)
    App(**config["mysql"])()
