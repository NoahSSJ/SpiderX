from pathlib import Path
import pytest
import requests
import sys
sys.path.append(str(Path(__file__).parent.parent.resolve()))
from src.core.bilibili import BiliBiliSpider
from src.utils import *
from src.client import *
from src.config import Mode

log = setup_logger(task_name="test")

def test_bili_api():
    response = BiliBiliSpider(url='1').check_api()
    code = response.json()['code']
    assert code == 0

def test_weibo_api():
    pass

def test_youtube_api():
    pass

def test_xhs_api():
    pass

def test_connect_redis():
    r = build_redis()
    assert r.ping() == True

def test_connect_mysql():
    conn = build_db()
    assert conn.is_connected() == True

def test_connect_oss():
    pass

def test_find_env():
    flag = find_env()
    assert isinstance(flag, Path)

