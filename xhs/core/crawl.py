import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import pickle
from pprint import pformat, pprint
import random
import time
import os
from urllib.parse import urlencode
import requests
from .encrypt import XS
from lxml import etree
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import redis
import sqlite3
from dotenv import load_dotenv

load_dotenv()

def setup_logger(task_name: str = "xhs") -> logging.Logger:
    root_dir = next((dir for dir in Path(__file__).resolve().parents if dir.joinpath('a.txt').exists()), None)
    log_dir = root_dir / "logs" / task_name
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir.joinpath('run.log')
    logger = logging.getLogger(name=task_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger
    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(filename)s:%(lineno)d | "
        "%(funcName)s | " + '\n'
        "%(message)s"
    )
    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

log = setup_logger()

class XhsSpider():
    session = requests.Session()
    session.headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'origin': 'https://www.xiaohongshu.com',
        'priority': 'u=1, i',
        'referer': 'https://www.xiaohongshu.com/',
        'sec-ch-ua': '"Chromium";v="154", "Microsoft Edge";v="154", "Not A(Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36 Edg/154.0.0.0',
        'x-b3-traceid': '515c6068e2e8fb58',
        'x-rap-param': 'ByQBBQAAAAEAAAAUAAABdK0BE1QAACg9AAAAGAAAAAAAAAAAcHlwYzCMgZP8WrPBnVcsH657l4jlAAAAEFupwS2rV/itNiAjDNGBmKzjDGM+RHoq5rYDaRdDR7rW5MkSmv+WoJqr5Fxif4sDWVxP+uTkdoGQIbko+kDBDElkEqNiRCPkIqsh+8pcpx6bBtnsm/jD7YaThqrqtErXtFNWqoGPyifhOhsA0Aus4nFsrcyWXetGvIPcY5uUnuCPExhRloV3Exk73YdzkJIRSGe/EwhHgW6TEcN25yI18wpkTcocy3TsKdm8Rl6DgP3O+uKTp8q9+HyRO5LPPwxMRifJUvVNd+W5Xws0XJiiX6cB3uV2uscC5+qZdLP8uCyopwwGpExgXCop/BfRqMT06PqIQFW/05rPAmN+IFI8aZkzwZG0+SOWP9oq5tDALNV1M6WnzUuBBbgjI3ECSOMC4CPjhmFhpHRl24jBkb1g3krbW8havFjnaYtQFMi/Ji218NCkPVlZ6D8xZQIa8+hpCzt5/JZvdUwd5Thu5MbGC/W+jZNjo86VEMspEt0Ip7flAAABaw==',
        'x-s-common': '2UQAPsHC+aIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1+shAHjIj2eHjwjQgynEDJ74AHjIj2ePjwjQhyoPTqBPT49pjHjIj2ecjwjH9N0L9N0PjNsQh+aHCH0bYPBLEG/GF+ebf2o4DqopAJgS7yAp0q9l1wnpf8diA47iI2040+fuF+/ZIPeZUw/WMPADjNsQh+jHCHjHVHdW7H0ijHjIj2eWjwjQQPAYUaBzdq9k6qB4Q4fpA8b878FSet9RQzLlTcSiM8/+n4MYP8FMMHjIj2eDjwjF7+/qFP/ZIPePVHdWlPsHCPsIj2erlH0ijJfRUJnbVHjIj2erUH0ijP/qEPeDMPeZh+/GI+eVl+ADIP0HM+/DF+ecUHdF=',
        'x-xray-traceid': 'd07e78d051cbdaead6d120c734a88d77',
        'cookie': 'abRequestId=e4f552dd-c9d6-53dd-93ac-2f6df6d4e2fc; ets=1790626382778; a1=1a0e9a6441fxwdpusmywk5csln9effz3wz0z7c6o450000298539; webId=971f437727d38507054dfe905df988f0; gid=y08dj0KWDyEJy08dj0K44uSKyiCEfU7M6vET8l42SM1Iju28diiuqW888JjY2qj8j88S0d0i; xsecappid=xhs-pc-web; last_web_session=040069b83512899baab34731f7384b0811412c; web_session=040069b0de1d7812247f0831f7384bfcffda35; id_token=VjEAAH3eXW+fDLlgLeeUTr29IBlLIOt356fypKh/mJtU1hbuMA1wLUgZvtn9vGqjSuwsLyoNc99hvHnqC/qqIi4IBJpktd5+Rjj7Z8ppDTCw10KqhnPL6KUf6NatzyxTMIufBim4; x-rednote-datactry=CN; x-rednote-holderctry=CN; webBuild=6.56.3; acw_tc=0a0b101317911650174625386e73dbb805fc6e2b2f5b4a048b5fa4835b9e24; websectiga=cffd9dcea65962b05ab048ac76962acee933d26157113bb213105a116241fa6c; sec_poison_id=c52b61e9-10a5-430c-bb7b-3e9a45ded4c5; unread={%22ub%22:%226aba1b220000000014000b5c%22%2C%22ue%22:%226ac23328000000001a031e0b%22%2C%22uc%22:25}; loadts=1791165046756',
    }

    r = redis.Redis(
        host=os.getenv('hostname'),
        port=6379,
        db=0,
        password=os.getenv('passwd'),
        decode_responses=True,
        protocol=2,
    )

    session.proxies = {

    }
    signer = XS()

    def __init__(self, url: str = 'https://www.xiaohongshu.com/user/profile/648a92c1000000002a037537?xsec_token=ABvwrm2wLnOaqJvyKTlRaH1nQh5Fgo-mJQYvrUQzTl57E=&xsec_source=pc_like'):
        self.homepage_url = url
        self.uid = url.split('?')[0].split('/')[-1]
        self.xsec_token = url.split('xsec_token=')[-1].split('&')[0]
        self.note_cnt = 0
        self.name = self.get_name()

    def get_name(self):
        response = self.session.get(url=self.homepage_url)
        response.encoding = response.apparent_encoding
        html = etree.HTML(response.text)
        name = html.xpath("//title/text()")[0]
        return name

    def generate_urls(self):
        response = self.session.get(url=self.homepage_url)
        pattern = r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;?\s*</script>"
        match = re.search(pattern, response.text, re.S)
        json_str = match.group(1)
        json_str = json_str.replace(':undefined', ':null').replace('new Set([])', '[]')
        json_dict = json.loads(json_str)
        for index, item in enumerate(json_dict['user']['notes'][0], start=1):
            note_id = item['noteCard']['noteId']
            xsec_token = item['noteCard']['xsecToken']
            # title = item['display_title']
            url = f'https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_like'
            yield url
            self.note_cnt += 1
        cursor = url.split('/')[-1].split('?')[0]
        params = {
            "num": "30",
            "cursor": cursor,
            "user_id": "5ec90017000000000101f887",
            "image_formats": "jpg,webp,avif",
            "xsec_token": self.xsec_token,
            "xsec_source": "pc_like",
        }
        while True:
            url = 'https://edith.xiaohongshu.com/api/sns/web/v1/user_posted'
            path = '/' + url.split('/', 3)[3] + '?' + urlencode(params)
            self.session.headers.update(self.signer.generate(path, self.session.headers['cookie']))
            response = self.session.get(url, params=params)
            pprint(response.json())
            cursor = response.json()['data']['cursor']
            has_more = response.json()['data']['has_more']
            print('--------------------------------')
            print(cursor)
            print(has_more)
            print('----------------------------------')
            for index, item in enumerate(response.json()['data']['notes'], start=1):
                note_id = item['note_id']
                xsec_token = item['xsec_token']
                # title = item['display_title']
                url = f'https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_like'
                yield url
                self.note_cnt += 1
            params['cursor'] = cursor
            
            time.sleep(random.uniform(3, 10))
            if has_more == False:
                log.info(self.note_cnt)
                return

    def process_urls(self):
        for index, url in enumerate(self.generate_urls(), start=1):
            if self.r.sadd("seen_urls", url):
                log.info(f"{url}入队")
                self.r.lpush('url_queue', url)
            if index == 3:
                return

    def consume_urls(self):
        while True:
            url = self.r.rpop('url_queue')
            if url is None:
                break
            log.info(f"正在消费{url}")
            yield url

    def parse_url(self, url):
        response = self.session.get(url=url)
        pattern = r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;?\s*</script>"
        match = re.search(pattern, response.text, re.S)
        json_str = match.group(1)
        json_str = json_str.replace(':undefined', ':null').replace('new Map([])', '{}')
        json_str = json_str.rstrip().removesuffix(',')
        json_dict = json.loads(json_str)
        data = json_dict['feed']['undertakeNote']
        # pprint(data)
        title = data['items'][0]['noteCard']['title']
        desc = data['items'][0]['noteCard']['desc']
        tags = ','.join([i['name'] for i in data['items'][0]['noteCard']['tagList']])
        image_list = []
        video_list = []
        for index, item in enumerate(data['items'][0]['noteCard']['imageList'], start=1):
            image_url = item['urlDefault']
            image_bytes = requests.get(image_url, headers=self.session.headers).content
            image_list.append(image_bytes)
        # log.info(title)
        # log.info(url)
        # log.info(image_list)
        kwargs = {
            "uid": self.uid,
            "name": self.name,
            "title": title,
            "image_list": image_list,
            "video_list": video_list
        }
        log.info(pformat(kwargs))
        yield kwargs
        # conn = sqlite3.connect("xhs.db")
        # conn.execute("""
        #     CREATE TABLE IF NOT EXISTS wk (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         title TEXT NOT NULL,
        #         image_list BLOB,
        #         video_list BLOB
        #     )
        # """)
        # conn.execute("""INSERT INTO wk (title, image_list, video_list) VALUES (?, ?, ?)""", (title, pickle.dumps(image_list), pickle.dumps(video_list)))
        # conn.commit()






            

if __name__ == '__main__':
    a = XhsSpider()
    # a.get_page()
    # a.get_user()
    # print(next(a.generate_urls()))
    a.process_urls()
