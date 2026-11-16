import math
import uuid
import redis
import requests
import re
from typing import Any, ClassVar
from urllib.parse import quote
import json
import sys
import os
import time
import hashlib
import base64
import socket
import logging
from logging.handlers import RotatingFileHandler
from pprint import pprint
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class SearchParams():
    pn: int
    mid: int
    _FIXED: ClassVar[dict] = {
        "ps": 40,
        "tid": 0,
        "special_type": "",
        "order": "pubdate",
        "index": 0,
        "keyword": "",
        "order_avoided": "true",
        "platform": "web",
        "space_login_group": 1,
        "web_location": "333.1387",
        "x-bili-locale-json": "{\"c_locale\":{\"language\":\"zh\",\"script\":\"Hans\"},\"always_translate\":false}",
        "x-bili-device-req-json": "{\"platform\":\"web\",\"device\":\"pc\",\"spmid\":\"333.1387\",\"mobi_app\":\"web_cn\"}",
    }
    _NEED_SIGN: ClassVar[bool] = True
    _NEED_FINGERPRINT: ClassVar[bool] = True

@dataclass
class ReplyParams():
    oid: int
    offset: str
    _FIXED = {
        'type': '1',
        'mode': '3',
        'pagination_str': '{"offset":""}',
        'plat': '1',
        'seek_rpid': '',
        'web_location': '1315875',
        'x-bili-locale-json': '{"c_locale":{"language":"zh","script":"Hans"},"always_translate":false}',
    }
    _NEED_SIGN: ClassVar[bool] = True
    _NEED_FINGERPRINT: ClassVar[bool] = False


FINGERPRINT = {
    # 原始编码值
    "dm_img_list": "[{\"x\":876,\"y\":1053,\"z\":0,\"timestamp\":2848,\"k\":116,\"type\":0},{\"x\":903,\"y\":1073,\"z\":25,\"timestamp\":4498,\"k\":112,\"type\":0},{\"x\":1008,\"y\":1178,\"z\":130,\"timestamp\":4758,\"k\":70,\"type\":1},{\"x\":2881,\"y\":-1886,\"z\":162,\"timestamp\":275282,\"k\":94,\"type\":0},{\"x\":3247,\"y\":-946,\"z\":416,\"timestamp\":275382,\"k\":126,\"type\":0},{\"x\":2737,\"y\":87,\"z\":337,\"timestamp\":276519,\"k\":64,\"type\":0},{\"x\":2665,\"y\":-448,\"z\":251,\"timestamp\":276620,\"k\":60,\"type\":0},{\"x\":2697,\"y\":-440,\"z\":286,\"timestamp\":276721,\"k\":83,\"type\":0},{\"x\":3074,\"y\":-70,\"z\":684,\"timestamp\":276830,\"k\":63,\"type\":0},{\"x\":3400,\"y\":242,\"z\":1006,\"timestamp\":276976,\"k\":83,\"type\":0},{\"x\":3075,\"y\":-161,\"z\":662,\"timestamp\":277079,\"k\":67,\"type\":0},{\"x\":2880,\"y\":-352,\"z\":478,\"timestamp\":277182,\"k\":106,\"type\":0},{\"x\":2569,\"y\":-774,\"z\":178,\"timestamp\":277286,\"k\":80,\"type\":0},{\"x\":3634,\"y\":289,\"z\":1249,\"timestamp\":277391,\"k\":73,\"type\":0},{\"x\":2480,\"y\":-1210,\"z\":164,\"timestamp\":277496,\"k\":109,\"type\":0},{\"x\":3261,\"y\":-810,\"z\":1030,\"timestamp\":277599,\"k\":82,\"type\":0},{\"x\":3339,\"y\":-813,\"z\":1098,\"timestamp\":277703,\"k\":64,\"type\":0},{\"x\":4129,\"y\":-65,\"z\":1876,\"timestamp\":277812,\"k\":78,\"type\":0},{\"x\":2370,\"y\":-1824,\"z\":117,\"timestamp\":745267,\"k\":101,\"type\":1},{\"x\":1940,\"y\":2138,\"z\":1070,\"timestamp\":745515,\"k\":77,\"type\":0},{\"x\":3854,\"y\":2941,\"z\":2269,\"timestamp\":745619,\"k\":75,\"type\":0},{\"x\":2837,\"y\":1423,\"z\":1076,\"timestamp\":745732,\"k\":67,\"type\":0},{\"x\":2655,\"y\":1241,\"z\":894,\"timestamp\":745864,\"k\":78,\"type\":0},{\"x\":2392,\"y\":697,\"z\":531,\"timestamp\":745967,\"k\":85,\"type\":0},{\"x\":3328,\"y\":1352,\"z\":1436,\"timestamp\":746068,\"k\":77,\"type\":0},{\"x\":3951,\"y\":1368,\"z\":2017,\"timestamp\":746172,\"k\":64,\"type\":0},{\"x\":2327,\"y\":-442,\"z\":376,\"timestamp\":746276,\"k\":79,\"type\":0},{\"x\":2281,\"y\":-682,\"z\":314,\"timestamp\":746376,\"k\":81,\"type\":0},{\"x\":4763,\"y\":1807,\"z\":2752,\"timestamp\":746481,\"k\":75,\"type\":0},{\"x\":5428,\"y\":2012,\"z\":3302,\"timestamp\":746584,\"k\":108,\"type\":0},{\"x\":5635,\"y\":1688,\"z\":3400,\"timestamp\":746685,\"k\":125,\"type\":0},{\"x\":4512,\"y\":391,\"z\":2224,\"timestamp\":746789,\"k\":61,\"type\":0},{\"x\":5679,\"y\":1422,\"z\":3339,\"timestamp\":746896,\"k\":101,\"type\":0},{\"x\":3517,\"y\":-736,\"z\":1165,\"timestamp\":747009,\"k\":122,\"type\":0}]",
    "dm_img_str": "V2ViR0wgMS4wIChPcGVuR0wgRVMgMi4wIENocm9taXVtKQ",
    "dm_cover_img_str": "QU5HTEUgKE5WSURJQSwgTlZJRElBIEdlRm9yY2UgUlRYIDQwNzAgTGFwdG9wIEdQVSAoMHgwMDAwMjg2MCkgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wLCBEM0QxMSlHb29nbGUgSW5jLiAoTlZJRElBKQ",
    "dm_img_inter": "{\"ds\":[{\"t\":7,\"c\":\"dnVpX2J1dHRvbiB2dWlfYnV0dG9uLS1hY3RpdmUgdnVpX2J1dHRvbi0tYWN0aXZlLWJsdWUgdnVpX2J1dHRvbi0tbm8tdHJhbnNpdGlvbiB2dWlfcGFnZW5hdGlvbi0tYnRuIHZ1aV9wYWdlbmF0aW9uLS1idG4tbn\",\"p\":[5391,25,9362],\"s\":[160,330,320]}],\"wh\":[2686,1327,66],\"of\":[5477,7316,20]}"
}

def setup_logger(task_name: str = "bilibili") -> logging.Logger:
    log_dir = Path(__file__).parent.parent.resolve() / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir.joinpath(f'{task_name}.log')
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
        "%(process)d | "
        "%(threadName)s | "
        "%(filename)s:%(lineno)d | "
        "%(funcName)d | "
        "%(message)s",
        defaults={"hostname": f"{socket.gethostname()}"}
    )
    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes= 10 * 1024 * 1024,
        backupCount=3,
        encoding='utf-8'
    )
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
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
        'sec-ch-ua': '"Not-A.Brand";v="99", "Microsoft Edge";v="157", "Chromium";v="157"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36 Edg/157.0.0.0',
        'cookie': 'buvid3=61979FAF-5F46-4CE9-8DFA-101F02B42D3C28770infoc; b_nut=1790103228; _uuid=C1B641B10-21D10-92101-5A38-1D59BFDBBCDD28491infoc; buvid_fp=3aa6c2513671b9ae8a99a7d8f42cad77; buvid4=6794B7FF-C6B9-0C32-E3EE-AA5EB5A34E1131365-026092302-/KtPZeHW9gETm7AfGjVxMQ%3D%3D; DedeUserID=688319368; DedeUserID__ckMd5=5f5dc4f07ec63413; rpdid=0zbfAGyzmN|HQ6Ng9TF|1GZ|3w1X96jl; LIVE_BUVID=AUTO1717901073244675; user_site=CN; default_sites=%5B%22CN%22%2C%22OVERSEAS%22%5D; CURRENT_QUALITY=80; SESSDATA=f41bc391%2C1810212380%2C46a2d%2Ab2CjCOBGuwoXn8CFe0kIPlHWvVgmdQTSS1OMHX7bmuSJdLx0hvy2tcxyvECJnYjbgrfCoSVkNNRjk0R3NoN1piNEphRnZmN2h3R3dLdjNLcmVIYTRKNVRLVUZwUk5vN25pZ0tVQjRoajM3X3kzT1ppdXhPMWZOaDhVeWVCVnZybUZwMGZua0piZU5nIIEC; bili_jct=06c7af31e2261ba9b915aec371a9ca73; home_feed_column=5; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTUwMTM4MTcsImlhdCI6MTc5NDc1NDU1NywicGx0IjotMX0.__4mXMzOnfmsFA0om8YBWaxybE2VT3o-JCAx9doIOUc; bili_ticket_expires=1795013757; browser_resolution=1530-731; sid=4njal18r; bp_t_offset_688319368=1271105518395457536; CURRENT_FNVAL=2000; b_lsid=C6217167_1A1E1DE0821',
    }
    session.proxies = {}

    def __init__(self):
        pass

    def get_wbi_key(self):
        response = self.session.get(url='https://api.bilibili.com/x/web-interface/nav')
        # pprint(response.json())
        img_key = response.json()['data']['wbi_img']['img_url'].split('/')[-1].split('.')[0]
        sub_key = response.json()['data']['wbi_img']['sub_url'].split('/')[-1].split('.')[0]
        # log.debug(img_key, sub_key)
        wbi_key = img_key + sub_key
        return wbi_key

    def get_fingerprint(self):
        pass

    def signed_params(self, params: dict) -> dict[str, Any]:
        key = self.get_wbi_key()
        indices = [
            46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
            27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
            37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
            22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
        ]
        i = "".join(key[i] for i in indices if i < len(key))[:32]
        params['wts'] = int(time.time() + 0.5)
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
        w_rid = hashlib.md5((u + i).encode('utf-8')).hexdigest()
        params['w_rid'] = w_rid
        return params

    def build_params(self, baseParams: object) -> dict[str, Any]:
        params = asdict(baseParams)
        print(baseParams._NEED_FINGERPRINT)
        if baseParams._FIXED:
            params.update(baseParams._FIXED)
        if baseParams._NEED_FINGERPRINT:
            params.update(FINGERPRINT)
        if baseParams._NEED_SIGN:
            params = self.signed_params(params)
        return params

    def generate_urls(self):
        end = None
        pn = 1
        while True:
            base_params = SearchParams(pn=pn, mid=1166997747)
            params = self.build_params(baseParams=base_params)
            response = self.session.get('https://api.bilibili.com/x/space/wbi/arc/search', params=params)
            # pprint(response.json())
            if end is None:
                end = math.ceil(response.json()['data']['page']['count'] / 40)
            for item in response.json()['data']['list']['vlist']:
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
                yield kwargs
            pn += 1
            print('------------------------------')
            if pn > end:
                return

    def process_urls(self):
        for index, kwargs in enumerate(self.generate_urls(), start=1):
            url = kwargs['url']
            if self.r.sadd("bili_set", url):
                log.info(f"第{index}个url入队，url:{url}")
                json_str = json.dumps(kwargs, ensure_ascii=False, indent=2)
                self.r.lpush("bili_list", json_str) 

    def parse_url(self):
        pass

    
a = BiliBiliSpider()
print(next(a.generate_urls()))


    

    




    