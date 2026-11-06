from enum import Enum
import logging
from logging.handlers import RotatingFileHandler
import base64
import hashlib
from pathlib import Path
import socket
import sys
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
sys.path.append(str(Path(__file__).parent.parent.resolve()))
from src.config import SRC_DIR

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

def find_env() -> Path | None:
    cur_dir = Path(__file__).parent.resolve()
    while True:
        env_path = cur_dir / '.env'
        if env_path.exists():
            return env_path
        if cur_dir.parent == cur_dir:   
            return None
        cur_dir = cur_dir.parent


def setup_logger(task_name: str = "bilibili"):
    log_dir = SRC_DIR / "log" / task_name
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir.joinpath('run.log')
    logger = logging.getLogger(task_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger
    formatter = logging.Formatter(
        fmt=
        "%(asctime)s | "
        "%(hostname)s | "
        "%(process)d | "
        "%(threadName)s | "
        "%(levelname)s | "
        "%(filename)s:%(lineno)d | "
        "%(funcName)s | "
        "%(message)s",
        defaults={"hostname": f'{socket.gethostname()}'},
    )
    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger