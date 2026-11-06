from pathlib import Path
import random
import threading
import requests
import logging
from logging.handlers import RotatingFileHandler
import json
from pprint import pprint
import sys
import os
import time
import re
import hashlib
from urllib.parse import quote
from lxml import etree
from pprint import pformat
import mysql.connector
import redis
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import socket
import uuid
from dotenv import load_dotenv
sys.path.append(str(Path(__file__).parent.parent.parent.resolve()))
from src.client import build_db, build_redis

load_dotenv()

SRC_DIR = next((dir / "src" for dir in Path(__file__).resolve().parents if dir.joinpath('requirements.txt').exists()), None)

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

log = setup_logger()

class BiliBiliSpider():
    session = requests.Session()
    session.headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'origin': 'https://space.bilibili.com',
        'priority': 'u=1, i',
        'referer': 'https://space.bilibili.com/1166997747/upload/video',
        'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
        'cookie': "buvid3=7D635C11-7648-0B92-F51C-4F32593660A603269infoc; b_nut=1790153403; _uuid=EF58C87B-92DE-789C-52106-4C95F2F13A10C03506infoc; buvid_fp=561dfa36addd3c6e81e3fab7a3dc8ddc; home_feed_column=4; browser_resolution=1272-668; buvid4=A6B5704E-AD92-70CD-4C4F-D8530B32E7F504950-026092316-4p8iWDXLmUBr1VXCP/kzng%3D%3D; CURRENT_QUALITY=0; rpdid=|(umYu~kJYYk0J'u~m|ulJl~k; bsource=search_bing; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTIyOTE3OTgsImlhdCI6MTc5MjAzMjUzOCwicGx0IjotMX0.df8NNNQkV3d8q6PTQTWO8WKuUkyrHw9ygXiIEEQmI8U; bili_ticket_expires=1792291738; SESSDATA=81728145%2C1807584664%2C82464%2Aa1CjCSgBS2vUqHLKqawhGX9pd5N9MKJABe1mW-c3urUWJO7wjCke2_1mjRwkGZMV3QosASVkpHR1hOZUhtU1M1U0xWdy1aMVV6eVRxZ0ZrQ2MxWVhWcWlKVUk3bGVweUxDQ1RIYndzek1qS25BeWdCSTI3RFZMY1V0X0xMVTZQZ2ZPRUNaU1BjakJRIIEC; bili_jct=613efc1b0e06a2a4fdf7e3679b23228c; DedeUserID=688319368; DedeUserID__ckMd5=5f5dc4f07ec63413; CURRENT_FNVAL=4048; sid=7za7hbl0; b_lsid=10E3E4F8_1A13E4782A4",

    }
    session.proxies = {

    }

    save_dir = SRC_DIR / "download"
    save_dir.mkdir(parents=True, exist_ok=True)

    def __init__(self, url: str):
        self.url = url
        # self.conn = build_db()
        self.r = build_redis()
        
    def get_wbi_key(self):
        response = self.session.get(url='https://api.bilibili.com/x/web-interface/nav')
        # pprint(response.json())
        img_key = response.json()['data']['wbi_img']['img_url'].split('/')[-1].split('.')[0]
        sub_key = response.json()['data']['wbi_img']['sub_url'].split('/')[-1].split('.')[0]
        log.debug(img_key, sub_key)
        return img_key, sub_key

    def get_wid(self, params: dict):
        img_key, sub_key = self.get_wbi_key()
        tmp = img_key + sub_key
        indices = [
            46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
            27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
            37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
            22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
        ]
        i = "".join(tmp[i] for i in indices if i < len(tmp))[:32]
        r = int(time.time() + 0.5)
        params.pop('w_rid', None)
        params.pop('wts', None)
        params['wts'] = r
        s = sorted(params.keys())
        l = []
        for p in s:
            v = params[p]
            if v and isinstance(v, str):
                v = re.sub("[!'()*]", "", v)  
            if v is not None:
                v = str(v).lower() if isinstance(v, bool) else str(v)
                key = quote(str(p), safe="~()*!.'-")
                value = quote(v, safe="~()*!.'-")
                l.append(f"{key}={value}")

        u = "&".join(l)
        # print(u)
        w_rid = hashlib.md5((u + i).encode('utf-8')).hexdigest()
        # print(w_rid)
        wts = str(r)
        params['w_rid'] = w_rid
        params['wts'] = wts
        return params

    def generate_urls(self):
        params = {
            "pn": 1,
            "ps": 40,
            "tid": 0,
            "special_type": "",
            "order": "pubdate",
            "mid": 1166997747,
            "index": 0,
            "keyword": "",
            "order_avoided": "true",
            "platform": "web",
            "space_login_group": 1,
            "web_location": "333.1387",
            "x-bili-locale-json": "{\"c_locale\":{\"language\":\"zh\",\"script\":\"Hans\"},\"always_translate\":false}",
            "x-bili-device-req-json": "{\"platform\":\"web\",\"device\":\"pc\",\"spmid\":\"333.1387\",\"mobi_app\":\"web_cn\"}",
            "dm_img_list": "[{\"x\":876,\"y\":1053,\"z\":0,\"timestamp\":2848,\"k\":116,\"type\":0},{\"x\":903,\"y\":1073,\"z\":25,\"timestamp\":4498,\"k\":112,\"type\":0},{\"x\":1008,\"y\":1178,\"z\":130,\"timestamp\":4758,\"k\":70,\"type\":1},{\"x\":2881,\"y\":-1886,\"z\":162,\"timestamp\":275282,\"k\":94,\"type\":0},{\"x\":3247,\"y\":-946,\"z\":416,\"timestamp\":275382,\"k\":126,\"type\":0},{\"x\":2737,\"y\":87,\"z\":337,\"timestamp\":276519,\"k\":64,\"type\":0},{\"x\":2665,\"y\":-448,\"z\":251,\"timestamp\":276620,\"k\":60,\"type\":0},{\"x\":2697,\"y\":-440,\"z\":286,\"timestamp\":276721,\"k\":83,\"type\":0},{\"x\":3074,\"y\":-70,\"z\":684,\"timestamp\":276830,\"k\":63,\"type\":0},{\"x\":3400,\"y\":242,\"z\":1006,\"timestamp\":276976,\"k\":83,\"type\":0},{\"x\":3075,\"y\":-161,\"z\":662,\"timestamp\":277079,\"k\":67,\"type\":0},{\"x\":2880,\"y\":-352,\"z\":478,\"timestamp\":277182,\"k\":106,\"type\":0},{\"x\":2569,\"y\":-774,\"z\":178,\"timestamp\":277286,\"k\":80,\"type\":0},{\"x\":3634,\"y\":289,\"z\":1249,\"timestamp\":277391,\"k\":73,\"type\":0},{\"x\":2480,\"y\":-1210,\"z\":164,\"timestamp\":277496,\"k\":109,\"type\":0},{\"x\":3261,\"y\":-810,\"z\":1030,\"timestamp\":277599,\"k\":82,\"type\":0},{\"x\":3339,\"y\":-813,\"z\":1098,\"timestamp\":277703,\"k\":64,\"type\":0},{\"x\":4129,\"y\":-65,\"z\":1876,\"timestamp\":277812,\"k\":78,\"type\":0},{\"x\":2370,\"y\":-1824,\"z\":117,\"timestamp\":745267,\"k\":101,\"type\":1},{\"x\":1940,\"y\":2138,\"z\":1070,\"timestamp\":745515,\"k\":77,\"type\":0},{\"x\":3854,\"y\":2941,\"z\":2269,\"timestamp\":745619,\"k\":75,\"type\":0},{\"x\":2837,\"y\":1423,\"z\":1076,\"timestamp\":745732,\"k\":67,\"type\":0},{\"x\":2655,\"y\":1241,\"z\":894,\"timestamp\":745864,\"k\":78,\"type\":0},{\"x\":2392,\"y\":697,\"z\":531,\"timestamp\":745967,\"k\":85,\"type\":0},{\"x\":3328,\"y\":1352,\"z\":1436,\"timestamp\":746068,\"k\":77,\"type\":0},{\"x\":3951,\"y\":1368,\"z\":2017,\"timestamp\":746172,\"k\":64,\"type\":0},{\"x\":2327,\"y\":-442,\"z\":376,\"timestamp\":746276,\"k\":79,\"type\":0},{\"x\":2281,\"y\":-682,\"z\":314,\"timestamp\":746376,\"k\":81,\"type\":0},{\"x\":4763,\"y\":1807,\"z\":2752,\"timestamp\":746481,\"k\":75,\"type\":0},{\"x\":5428,\"y\":2012,\"z\":3302,\"timestamp\":746584,\"k\":108,\"type\":0},{\"x\":5635,\"y\":1688,\"z\":3400,\"timestamp\":746685,\"k\":125,\"type\":0},{\"x\":4512,\"y\":391,\"z\":2224,\"timestamp\":746789,\"k\":61,\"type\":0},{\"x\":5679,\"y\":1422,\"z\":3339,\"timestamp\":746896,\"k\":101,\"type\":0},{\"x\":3517,\"y\":-736,\"z\":1165,\"timestamp\":747009,\"k\":122,\"type\":0}]",
            "dm_img_str": "V2ViR0wgMS4wIChPcGVuR0wgRVMgMi4wIENocm9taXVtKQ",
            "dm_cover_img_str": "QU5HTEUgKE5WSURJQSwgTlZJRElBIEdlRm9yY2UgUlRYIDQwNzAgTGFwdG9wIEdQVSAoMHgwMDAwMjg2MCkgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wLCBEM0QxMSlHb29nbGUgSW5jLiAoTlZJRElBKQ",
            "dm_img_inter": "{\"ds\":[{\"t\":7,\"c\":\"dnVpX2J1dHRvbiB2dWlfYnV0dG9uLS1hY3RpdmUgdnVpX2J1dHRvbi0tYWN0aXZlLWJsdWUgdnVpX2J1dHRvbi0tbm8tdHJhbnNpdGlvbiB2dWlfcGFnZW5hdGlvbi0tYnRuIHZ1aV9wYWdlbmF0aW9uLS1idG4tbn\",\"p\":[5391,25,9362],\"s\":[160,330,320]}],\"wh\":[2686,1327,66],\"of\":[5477,7316,20]}"
        }
        while True:
            params = self.get_wid(params=params)
            response = self.session.get('https://api.bilibili.com/x/space/wbi/arc/search', params=params)
            for index, item in enumerate(response.json()['data']['list']['vlist'], start=1):
                trace_id = str(uuid.uuid4())
                bvid = item['bvid']
                aid = item['aid']
                mid = item['mid']
                url = f"https://www.bilibili.com/{bvid}?vd_source=cd2f30c4c2b17931e5fe4b95752072ee"
                kwargs = {
                    "trace_id": trace_id,
                    "bvid": bvid,
                    "aid": aid,
                    "mid": mid,
                    "url": url
                }
                log.info(pformat(kwargs))
                yield kwargs
            params['pn'] += 1
            if params['pn'] == 3:
                return
                     
    def process_urls(self):
        for index, kwargs in enumerate(self.generate_urls(), start=1):
            url = kwargs['url']
            if self.r.sadd("bili_set", url):
                log.info(f"第{index}个url入队，url:{url}")
                json_str = json.dumps(kwargs, ensure_ascii=False, indent=2)
                self.r.lpush("bili_list", json_str)
            
    def parse_comment_url(self, aid: str):
        loop_index = 0
        params = {
            'oid': aid,
            'type': '1',
            'mode': '3',
            'pagination_str': '{"offset":""}',
            'plat': '1',
            'seek_rpid': '',
            'web_location': '1315875',
            'x-bili-locale-json': '{"c_locale":{"language":"zh","script":"Hans"},"always_translate":false}',
            'w_rid': '1c17932a577072da0cf8744afaf11f8c',
            'wts': '1792032775',
        }
        while True:
            time.sleep(random.uniform(3, 5))
            params = self.get_wid(params)
            response = self.session.get('https://api.bilibili.com/x/v2/reply/wbi/main', params)
            # log.info(pformat(response.json()))
            # pprint(response.json())
            next_offset = response.json()['data']['cursor']['pagination_reply'].get('next_offset')
            for index, item in enumerate(response.json()['data']['replies']):
                text = item['content']['message']
                kwargs = {
                    "text": text
                }
                yield kwargs
            log.info('-------------------------------------------------------')
            params['pagination_str'] = f'{{"offset":"{next_offset}"}}'
            loop_index += 1
            if loop_index > 3:
                return
            if next_offset is None:
                return
    
    # def storage(self):
    #     kwargs = 
    
    def worker(self):
        while True:
            json_tuple = self.r.brpop("bili_list", timeout=5)
            if json_tuple is None:
                break
            json_dict = json.loads(json_tuple[1])
            aid = json_dict['aid']
            try:
                for i in self.parse_comment_url(aid):
                    log.info(i)
            except Exception as e:
                log.info(e)
                
def run_pipline():
    s = BiliBiliSpider('1')
    s.process_urls()
    exit()
    with ThreadPoolExecutor(max_workers=1) as pool:
        futures = [pool.submit(s.worker) for _ in range(1)]
        for future in as_completed(futures):
            log.info(future.result())
    
        

    # @classmethod
    # def run_pipline(cls, params: dict, flag: int):
    #     instance = BiliBiliSpider('1')
    #     if flag == 1:
    #         instance.process_urls(params)
    #     else:
    #         json_tuple = instance.r.brpop("bili_list", timeout=5)
    #         json_dict = json.loads(json_tuple[1])
    #         pprint(json_dict)

  
                
if __name__ == "__main__":
    run_pipline()
    # while True:
    #     time.sleep(3)
    #     print('123')
    # log.info(1)
