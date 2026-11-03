"""小红书请求加密参数计算。"""

import base64
import hashlib
import json
import random
import struct
import time

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


class XS:
    """生成 x-s 及配套的 x-t；同一会话复用实例以递增计数器。"""

    def __init__(self, counter=25, global_count=1358,
                 fingerprint=bytes.fromhex('01edf9416767c9b583635e0744fa8415')):
        # 默认值沿用现有环境快照，可按实际浏览器环境传入。
        self.counter = counter
        self.global_count = global_count
        self.fingerprint = fingerprint

    def generate(self, path, cookie, body='', body_type=''):
        """path 为实际请求的路径及 query；body 为实际发送的文本，JSON 的 body_type 填 object。"""
        self.counter += 1
        cookies = dict(part.strip().split('=', 1) for part in cookie.split(';') if part.strip())
        timestamp = time.time_ns() // 1_000_000
        word = int(random.random() * 0xffffffff)
        mask = word & 255
        fingerprint = bytearray(self.fingerprint)
        fingerprint[1] = mask ^ 115
        digest = hashlib.md5((path + body).encode()).digest()
        tail = digest24(struct.pack('<Q', timestamp) + hashlib.md5(path.encode()).digest())
        packet = (
            bytes.fromhex('79686029')
            + struct.pack('<IQQIII', word, timestamp, int(cookies['loadts']),
                          self.counter, self.global_count, len((path + body).encode()))
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
        return {'x-s': xs, 'x-t': str(timestamp)}
