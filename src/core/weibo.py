import requests
import socket
import logging
import requests
import redis
import os
import json
from pathlib import Path
from logging.handlers import RotatingFileHandler
from pprint import pprint
from dotenv import load_dotenv
from enum import Enum

class Mode(Enum):
    MEDIA = 0
    COMMENT = 1

SRC_DIR = next((dir / "src" for dir in Path(__file__).resolve().parents if dir.joinpath('requirements.txt').exists()), None)

load_dotenv()

def setup_logger(task_name: str, level: int = 1) -> logging.Logger:
    match level:
        case 0: level = logging.DEBUG
        case 1: level = logging.INFO
    
    log_dir = SRC_DIR / "log" / task_name
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir.joinpath('run.log')
    logger = logging.getLogger(task_name)
    logger.setLevel(level)
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
        "%(funcName)s | \n"
        "%(message)s",
        defaults={"hostname": f'{socket.gethostname()}'}
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


log = setup_logger(task_name='1')
log.info('123')

class WeiboSpider():
    session = requests.Session()
    session.headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'client-version': 'v1.1.255',
        'priority': 'u=1, i',
        'referer': 'https://weibo.com/6015179439?refer_flag=1001030103_',
        'sec-ch-ua': '"Not:A-Brand";v="8", "Chromium";v="156", "Microsoft Edge";v="156"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'server-version': 'v2026.10.29.2',
        'traceparent': '00-5042f84250623b244bfc9c4fa7886a1e-760b69f16afea24a-00',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36 Edg/156.0.0.0',
        'x-requested-with': 'XMLHttpRequest',
        'x-xsrf-token': 'NdFsQ3wDVxhzdX1f8KFFu_Y1',
        'cookie': 'SCF=Ao13OC6Rt85UWOdDzVWUUKHePFVhXCq8C3W7ZypxTTvaOWB7XmAM_Ata6mZCDQV-bntF_ZJarC2eN1u2mXYghmQ.; SUB=_2A25H7dYpDeRhGeFJ4lUR9CvMyTyIHXVkg1fhrDV8PUNbmtANLRSlkW9Nfr-Ikm0-Rg2_hQ-Of0fJQ6L-zqoZFlWk; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9Wh1DLBSZYmiLfaEW7-PxKxc5NHD95QNS0.NehBfehz7Ws4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0M4S05XSK5Ee5tt; ALF=02_1796289401; XSRF-TOKEN=NdFsQ3wDVxhzdX1f8KFFu_Y1; WBPSESS=BWHVdTaHUrxrFPjSI85rtSHhHy60IqJ5jMnU_veNA6aGYytnnoXoSf6Fxw8UiQsAgJXJ_3KHyBqj_z7o7x6t51P9ns4clbCdfgvgE1ycJXWfv0OV-Q_ulmMdbKobTXWZbHptuMiFbpltmHxiyyrZ4A==; _s_tentry=weibo.com; Apache=9051794939521.111.1793703858928; SINAGLOBAL=9051794939521.111.1793703858928; ULV=1793703858930:1:1:1:9051794939521.111.1793703858928:',
    }
    session.proxies = {
        
    }

    def __init__(self, url='https://weibo.com/6015179439'):
        self.homepage_url = url
        self.uid = self.homepage_url.split('/')[-1] 
        self.save_dir = SRC_DIR / "download"
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.r = self.build_redis()

    def build_redis(self):
        r = redis.Redis(
            host=os.getenv('host'),
            port=6379,
            db=0,
            password=os.getenv('passwd'),
            decode_responses=True,
            socket_timeout=5
        )
        r.ping()
        return r

    def generate_urls(self):
        while True:
            params = {
                'uid': self.uid,
                'page': '1',
                'feature': '0',
            }
            response = self.session.get('https://weibo.com/ajax/statuses/mymblog', params=params)
            # pprint(response.json())
            since_id = response.json()['data']['since_id']
            params['since_id'] = since_id
            for item in response.json()['data']['list']:
                item_id = item['id']
                created_at = item['created_at']
                uid = item['user']['idstr']
                name = item['user']['screen_name']
                pic_ids = item.get('pic_ids')
                pic_infos = item.get('pic_infos')
                text_raw = item.get('text_raw')
                image_list = []
                video_list = []
                if pic_ids and pic_infos:
                    for id in pic_ids:
                        image_url = pic_infos[id]['large']['url']
                        image_list.append(image_url)
                        video_url = pic_infos[id].get('video')
                        video_list.append(video_url)
                        kwargs = {
                            "uid": uid,
                            "name": name,
                            "created_at": created_at,
                            "item_id": item_id,
                            "text": text_raw,
                            "image_list": image_list,
                            "video_list": video_list
                        }
                    yield kwargs

            return

    def process_urls(self):
        for index, kwargs in enumerate(self.generate_urls(), start=1):
            item_id = kwargs['item_id']
            if self.r.sadd("wb_set", item_id):
                log.info(f"第{index}个item入队，item_id：{item_id}")
                json_str = json.dumps(kwargs, ensure_ascii=False, indent=2)
                self.r.lpush("wb_list", json_str)

    def parse_url(self, kwargs, mode: int = 1):
        # pprint(kwargs)
        item_id = kwargs.get('item_id')
        uid = kwargs.get('uid')

        item_id = '5361502942660310'
        uid = '7335979459'

        match mode:
            case Mode.MEDIA.value:
                pass
            case Mode.COMMENT.value:
                print(1)
                params = {
                    'is_reload': '1',
                    'id': item_id,
                    'is_show_bulletin': '2',
                    'is_mix': '0',
                    'count': '10',
                    'uid': uid,
                    'fetch_level': '0',
                    'locale': 'zh-CN',
                }
                while True:
                    response = self.session.get('https://weibo.com/ajax/statuses/buildComments', params=params)
                    # pprint(response.json())
                    max_id = response.json().get('max_id')
                    params['max_id'] = max_id
                    text = ''
                    for item in response.json()['data']:
                        text += item['text_raw'] + '\n'
                    print(text)
                    if max_id == 0:
                        return

    def consumer(self):
        cnt = 0
        while True:
            json_tuple = self.r.brpop("wb_list", timeout=5)
            print(json_tuple)
            if json_tuple is None:
                break
            kwargs = json.loads(json_tuple[1])
            self.parse_url(kwargs)
            cnt += 1
            if cnt == 1:
                return


if __name__ == "__main__":
    a = WeiboSpider()
    # pprint(next(a.generate_urls()))
    # a.process_urls()
    # a.consumer()
    a.parse_url(kwargs={'a':1})
