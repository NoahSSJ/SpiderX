import os
import sys
import requests
import psutil
from dotenv import load_dotenv

load_dotenv()

WEBHOOK = os.getenv('fs')
PROCESS_NAME = '/root/some/bilibili.py'  # 建议用完整路径或唯一性强的片段

if not WEBHOOK:
    sys.exit("环境变量 fs 未配置")


def spider_alive():
    self_pid = os.getpid()
    for p in psutil.process_iter(['pid', 'cmdline']):
        if p.info['pid'] == self_pid:
            continue
        cmdline = p.info['cmdline']
        if not cmdline:
            continue
        if PROCESS_NAME in ' '.join(cmdline):
            return True
    return False


def send_alert():
    payload = {
        "msg_type": "text",
        "content": {"text": "⚠️ 进程断了，请检查服务器！"}
    }
    try:
        r = requests.post(WEBHOOK, json=payload, timeout=5)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"告警发送失败: {e}", file=sys.stderr)


if not spider_alive():
    send_alert()