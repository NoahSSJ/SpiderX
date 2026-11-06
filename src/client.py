import base64
import sys
import redis
import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.resolve()))
from src.utils import find_env

load_dotenv(dotenv_path=find_env())

def build_redis():
    r = redis.Redis(
        host=os.getenv('host'),
        port=6379,
        password=os.getenv('passwd'),
        db=0,
        decode_responses=True,
        socket_timeout=5
    )
    r.ping()
    return r

def build_db():
    conn = mysql.connector.connect(
        host=os.getenv('host'),
        port=3306,
        user="a0",
        password=os.getenv('passwd'),
        database="testdb",       
        charset="utf8mb4",    
    )
    # sql = """
    #     CREATE TABLE IF NOT EXISTS purchase (
    #         id INT PRIMARY KEY AUTO_INCREMENT,
    #         text VARCHAR(255) NOT NULL
    #     ) DEFAULT CHARSET=utf8mb4
    # """
    # cur = conn.cursor()
    # cur.execute(sql)
    # conn.commit()
    # cur.close()
    return conn

def build_oss():
    pass