import os
import uuid

import yt_dlp
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from pprint import pprint
import json
import socket
import redis
from pprint import pprint, pformat
from dotenv import load_dotenv

ROOT_DIR = next((dir for dir in Path(__file__).resolve().parents if dir.joinpath('pyproject.toml')), None)

load_dotenv()

def setup_logger(task_name: str) -> logging.Logger:
    log_dir = ROOT_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir.joinpath('run.log')
    logger = logging.getLogger(task_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    if logger.handlers:
        return logger
    formatter = logging.Formatter(
        fmt=
        "%(asctime)s | "
        "%(levelname)s | "
        "%(hostname)s | "
        "%(threadName)s | "
        "%(filename)s:%(lineno)d | "
        "%(funcName)s | "
        "%(message)s",
        defaults={"hostname": f'{socket.gethostname()}'}
    )
    file_handlder = RotatingFileHandler(
        filename=log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    console_handler = logging.StreamHandler()
    file_handlder.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handlder)
    logger.addHandler(console_handler)
    return logger

log = setup_logger("ytb")

def build_redis():
    r = redis.Redis(
        host=f'{os.getenv('host')}',
        port=6379,
        db=0,
        password=f'{os.getenv('passwd')}',
        decode_responses=True,
        socket_timeout=5
    )
    r.ping()
    return r

class YoutubeSpider():
    def __init__(self, url:str):
        self.channel_url = url
        self.r = build_redis()
        
    def generate_urls(self):
        ydl_opts = {
                "extract_flat": "in_playlist",  # 关键：只抓列表，不解析每个视频的流
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
            }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(self.channel_url, download=False)
            for index, item in enumerate(info["entries"], start=1):
                trace_id = str(uuid.uuid4())
                url = item['url']
                kwargs = {
                    "trace_id": trace_id,
                    "url": url
                }
                yield kwargs
                                
    def process_urls(self):
        for index, kwargs in enumerate(self.generate_urls(), start=1):
            url = kwargs['url']
            if self.r.sadd("ytb_set", url):
                json_str = json.dumps(kwargs, ensure_ascii=False, indent=2)
                self.r.lpush("ytb_queue", json_str)
                log.info(f"第{index}个元数据入队，url:{url}")
    
    def consumer_urls(self):
        while True:
            json_tuple = self.r.brpop("ytb_queue")
            if json_tuple is None:
                log.info("队列已经空了")
                break
            json_dict = json.loads(json_tuple[1])
            trace_id = json_dict['trace_id']
            url = json_dict['url']
            
    
        
        

a = YoutubeSpider("https://www.youtube.com/@ryan/videos")
# print(next(a.generate_urls()))
a.process_urls()

            