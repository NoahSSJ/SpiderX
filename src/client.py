import base64
import sqlite3
import sys
import redis
import mysql.connector
import os
from dotenv import load_dotenv
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.resolve()))
from src.utils import find_env
from src.config import DB_DIR

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

def build_mysql():
    conn = mysql.connector.connect(
        host=os.getenv('host'),
        port=3306,
        user="a0",
        password=os.getenv('passwd'),
        database="testdb",       
        charset="utf8mb4",    
    )
    return conn

def build_oss():
    pass

def build_db():
    db_path = DB_DIR.joinpath('cookie.db')
    conn = sqlite3.connect(db_path)
    sql = """
        CREATE TABLE IF NOT EXISTS cookie(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            jar_blob BLOB NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    conn.execute(sql)
    conn.commit()
    return conn
