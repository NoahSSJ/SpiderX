import base64
import redis
import mysql.connector
import os
import hashlib
from dotenv import load_dotenv
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

ROOT_DIR = next((dir for dir in Path(__file__).resolve().parents if dir.joinpath('requirements.txt').exists()), None)

def aes_encrypt(text: str, key: str):
    text = text.encode('utf-8')
    # iv = get_random_bytes(16)
    iv = bytes(16)
    key = hashlib.sha256(key.encode('utf-8')).digest()
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    cipher_bytes = cipher.encrypt(pad(text, AES.block_size))
    cipher_text = base64.b64encode(cipher_bytes).decode("ascii")
    print(cipher_text)
    return cipher_text

def aes_decrypt(cipher_text: str, key: str) -> str:
    iv = bytes(16)
    key = hashlib.sha256(key.encode("utf-8")).digest()
    cipher_bytes = base64.b64decode(cipher_text)
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    decrypt_bytes = cipher.decrypt(cipher_bytes)
    decrypt_text = unpad(
        decrypt_bytes,
        AES.block_size
    ).decode("utf-8")
    print(decrypt_text)
    return decrypt_text

def find_env() -> Path:
    cur_dir = Path(__file__).parent.resolve()
    while True:
        env_path = cur_dir.joinpath('.env')
        if env_path.exists():
            return env_path
        cur_dir = cur_dir.parent
        
        

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
        host="127.0.0.1",
        port=3306,
        user="root",
        # password=f"{os.getenv('passwd')}",
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

aaa = aes_encrypt(text='1234567890', key='123')
aes_decrypt(cipher_text=aaa, key='123')