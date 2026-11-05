from pprint import pformat, pprint
import re
from urllib.parse import urlencode

import requests
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import socket
import base64
import hashlib
import json
import random
import struct
import time
from lxml import etree
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.resolve()))
print(sys.path)
from src.client import *

SRC_DIR = next((dir / "src" for dir in Path(__file__).resolve().parents if dir.joinpath('requirements.txt').exists()), None)

STANDARD = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
MNS = 'MfgqrsbcyzPQRStuvC7mn501HIJBo2DEFTKdeNOwxWXYZap89+/A4UVLhijkl63G'
XYS = 'ZmserbBoHQtNP+wOcza/LpngG8yJq42KWYj0DSfdikx3VT16IlUAFM97hECvuRX5'
RC4_STATE = (
    108, 71, 200, 252, 102, 41, 228, 110, 198, 188, 243, 68, 179, 10, 96, 53,
    237, 46, 115, 61, 74, 185, 19, 217, 133, 212, 167, 205, 55, 111, 146, 116,
    201, 67, 151, 202, 229, 25, 178, 135, 235, 69, 112, 52, 195, 144, 78, 203,
    0, 83, 33, 231, 181, 140, 43, 175, 142, 248, 148, 145, 162, 187, 76, 88,
    2, 22, 77, 105, 16, 164, 139, 147, 124, 246, 121, 120, 176, 224, 44, 251,
    194, 31, 169, 218, 189, 95, 253, 155, 45, 223, 24, 150, 106, 249, 186, 126,
    23, 209, 191, 250, 92, 4, 90, 51, 21, 193, 196, 226, 183, 3, 210, 34,
    114, 129, 168, 99, 79, 15, 127, 40, 208, 32, 30, 27, 190, 1, 29, 220,
    14, 156, 119, 100, 60, 138, 214, 58, 234, 173, 87, 131, 104, 93, 221, 233,
    57, 9, 240, 75, 117, 177, 215, 152, 98, 232, 89, 174, 122, 38, 85, 8,
    206, 94, 70, 6, 109, 128, 5, 80, 18, 160, 182, 26, 101, 149, 28, 171,
    72, 227, 64, 137, 222, 199, 244, 219, 13, 225, 97, 184, 103, 241, 180, 165,
    132, 161, 7, 107, 39, 73, 170, 17, 130, 192, 236, 66, 118, 134, 211, 81,
    153, 207, 20, 197, 82, 48, 154, 254, 247, 56, 113, 143, 62, 172, 125, 49,
    245, 230, 242, 12, 65, 11, 36, 37, 63, 84, 238, 50, 86, 35, 141, 159,
    47, 239, 204, 216, 91, 59, 123, 54, 157, 158, 166, 255, 42, 163, 213, 136,
)

GLOBAL_COUNT = 1358
FINGERPRINT = bytes.fromhex('01edf9416767c9b583635e0744fa8415')


def b64(data, alphabet):
    return base64.b64encode(data).decode().translate(str.maketrans(STANDARD, alphabet))


def rotl(value, bits):
    value &= 0xffffffff
    return ((value << bits) | (value >> (32 - bits))) & 0xffffffff


def digest24(data):
    a, b = 0x6D2B79F5 ^ 24, 0x1B873593 ^ (24 << 8)
    c, d = 0x85EBCA6B ^ (24 << 16), 0xC2B2AE35 ^ (24 << 24)
    for x, y in struct.iter_unpack('<II', data):
        a = rotl((a + x) ^ c, 7)
        b = rotl((b ^ x) + d, 11)
        c = rotl((c + y) ^ a, 13)
        d = rotl((d ^ y) + b, 17)
    a ^= 24
    b ^= a
    c = (c + b) & 0xffffffff
    d ^= c
    a, b, c, d = rotl(a, 9), rotl(b, 13), rotl(c, 17), rotl(d, 19)
    a = (a + c) & 0xffffffff
    b ^= d
    c = (c + a) & 0xffffffff
    d ^= b
    return struct.pack('<IIII', a, b, c, d)


def rc4(data):
    state = list(RC4_STATE)
    i = j = 0
    result = bytearray()
    for value in data:
        i = (i + 1) & 255
        j = (j + state[i]) & 255
        state[i], state[j] = state[j], state[i]
        result.append(value ^ state[(state[i] + state[j]) & 255])
    return bytes(result)


def field(data):
    size = len(data)
    prefix = bytearray()
    while size >= 128:
        prefix.append((size & 127) | 128)
        size >>= 7
    return bytes(prefix) + bytes([size]) + data


def generate_xs(path, cookie, body='', body_type='', counter=25):
    """生成 x-s 及配套的 x-t；返回 (headers, 新的 counter)。"""
    counter += 1
    cookies = dict(part.strip().split('=', 1) for part in cookie.split(';') if part.strip())
    timestamp = time.time_ns() // 1_000_000
    word = int(random.random() * 0xffffffff)
    mask = word & 255
    fingerprint = bytearray(FINGERPRINT)
    fingerprint[1] = mask ^ 115
    digest = hashlib.md5((path + body).encode()).digest()
    tail = digest24(struct.pack('<Q', timestamp) + hashlib.md5(path.encode()).digest())
    packet = (
        bytes.fromhex('79686029')
        + struct.pack('<IQQIII', word, timestamp, int(cookies['loadts']),
                      counter, GLOBAL_COUNT, len((path + body).encode()))
        + bytes(value ^ mask for value in digest[:8])
        + field(cookies['a1'].encode()) + field(b'xhs-pc-web')
        + fingerprint + field(b'a3') + field(bytes(value ^ mask for value in tail))
    )
    envelope = {
        'x0': '4.4.3', 'x1': 'xhs-pc-web', 'x2': 'Windows',
        'x3': 'mns0301_' + b64(rc4(packet), MNS),
        'x4': body_type, 'x5': digest.hex(),
    }
    xs = 'XYS_' + b64(json.dumps(envelope, ensure_ascii=False, separators=(',', ':')).encode(), XYS)
    return {'x-s': xs, 'x-t': str(timestamp)}, counter

def setup_logger(task_name: str) -> logging.Logger:
    log_dir = SRC_DIR / "log" / task_name
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir.joinpath('run.log')
    logger = logging.getLogger(task_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if logger.handlers:
        return logger
    formatter = logging.Formatter(fmt=
        "%(asctime)s | "
        "%(levelname)s | "
        "%(hostname)s | "
        "%(process)d | "
        "%(threadName)s | "
        "%(filename)s:%(lineno)d | "
        "%(module)s | "
        "%(funcName)s |\n"
        "%(message)s",
        defaults={"hostname":f"{socket.gethostname()}"}
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

log = setup_logger(task_name='xhs')

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
    session.proxies = {}

    def __init__(self, url: str):
        self.homepage = url
        self.r = build_redis()
        self.uid = url.split('?')[0].split('/')[-1]
        self.xsec_token = url.split('xsec_token=')[-1].split('&')[0]
        self.note_cnt = 0
        self.name = self.get_name()
        # self.conn = build_db()


    def get_name(self):
        response = self.session.get(url=self.homepage)
        response.encoding = response.apparent_encoding
        html = etree.HTML(response.text)
        name = html.xpath("//title/text()")[0]
        return name

    def generate_urls(self):
        response = self.session.get(url=self.homepage)
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
            # self.session.headers.update(self.signer.generate(path, self.session.headers['cookie']))
            self.session.headers.update(generate_xs(path, self.session.headers['cookie']))
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
    a = XhsSpider(url='')
    # a.get_page()
    # a.get_user()
    # print(next(a.generate_urls()))
    a.process_urls()


