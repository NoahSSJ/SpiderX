import time
import requests
import base64
import io
import qrcode
from pprint import pprint

cookies = {
    "buvid3": "3C2AA53D-D01C-BF45-6C9E-BF6CF90A38D581396infoc",
    "b_nut": "1789307781",
    "_uuid": "65287D97-24B4-9324-23D5-9A6DFE5A7AA382715infoc",
    "buvid_fp": "b35c4cd866e73f239ea58d4c2d4287a2",
    "buvid4": "ED5D1FF3-0BD7-E6C9-F652-EA795C57C7BD82781-026091321-UCgj7X2OITSuRokPxoJVEqMCYGapUStHGm3LGPbdavzUuGYJADDwjZ4UiRrTfWWk",
    "bsource": "search_google",
    "user_site": "CN",
    "CURRENT_FNVAL": "2000",
    "sid": "o3fb1888",
    "home_feed_column": "4",
    "browser_resolution": "819-1111",
    "bili_ticket": "eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTQ0NjI4NDcsImlhdCI6MTc5NDIwMzU4NywicGx0IjotMX0.1Yqk8rtbcHU8RfFPtzzhvKGF1bj8CGoXu9oWHn2cXiY",
    "bili_ticket_expires": "1794462787",
    "DATE": "1794203649607",
    "umcr9xle": "U2FsdGVkX1+ZaNTBWBQPfMey+HVWXDSbSgBJBkkmDsbeg6NBSfY3jNQD45zhBT+V",
    "assva6": "U2FsdGVkX1+Z/Rzyw+m1tlkF2TRLnWEn2MHKlFagVNA=",
    "assva5": "U2FsdGVkX187JGx3yCf9S6FHDUsOBYla0r6xc9C7pCG/Pe/zPWd0Uxz4gKtJDe0RA3UlBHZvKJtCFBaAkGmgFw==",
    "crystal": "U2FsdGVkX19iTrqrtGYGAEBho5k+d94Cda0Louhmv/2gpYhQpeXMWbCyrrXNGcY0mqFpOHprEWAqSmwINUudi3PhPlOzlfobCKrFFV+oWZzx+Gw54Wr0Qjn0MJatM5PnsADDh4bbSJCu5+nRaXfMCZs94uzWRfOyuVwAc9kIiw/fwh0w8tttpDgcx87dSwu6eXOb2raIgRXWsd4LvCi0lrsZb4tBWsGUKobb8ya9zdT+H73DVAIHJT3SEptufzhK",
    "vmce9xdq": "U2FsdGVkX19M5+PJlps4VfCg4w+FqhHhQvUtYJoKhZeVJkfi1CFLmGuKRrW4nJlASQrn8Qk6tdgJbMfFNfMQO4zAlxYY0eRvthdsYRbZJ4euc7fNx+Yilfp1WR3qLZv8N+5AF4qAE7RGci+Fnr3A18dvakB89A0y4jXUWP1vlVg=",
    "cmci9xde": "U2FsdGVkX19fdeUBO6d1Ru9+ZsG1h8XJSAPKcknv+TCExEzZMAKHIXEWJb9MU/vnKObGFW8R6CVVA8C2ocGv/w==",
    "pmck9xge": "U2FsdGVkX19mWvj8nCMEyqKaVnDuurUYJkbe3TG5R6Y=",
    "b_lsid": "89D7DD28_1A1BEEFA6EC",
}

session = requests.Session()

session.headers = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "origin": "https://www.bilibili.com",
    "priority": "u=1, i",
    "referer": "https://www.bilibili.com/",
    "sec-ch-ua": '"Not-A.Brand";v="99", "Google Chrome";v="157", "Chromium";v="157"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/157.0.0.0 Safari/537.36"
    ),
}

# 关键：把浏览器 Cookie 装载到 Cookie Jar
for name, value in cookies.items():
    session.cookies.set(
        name,
        value,
        domain=".bilibili.com",
        path="/",
    )

generate_url = (
    "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
)

response = session.get(
    generate_url,
    params={
        "source": "main-fe-header",
        "go_url": "https://www.bilibili.com/",
        "web_location": "333.1007",
        "x-bili-redirect": "1",
        "x-bili-locale-json": (
            '{"c_locale":{"language":"zh","script":"Hans"},'
            '"always_translate":true}'
        ),
        "x-bili-device-req-json": (
            '{"platform":"web","device":"pc","spmid":"333.1007",'
            '"mobi_app":"web_cn"}'
        ),
    },
)

generate_data = response.json()
pprint(generate_data)

qrcode_key = generate_data["data"]["qrcode_key"]
login_url = generate_data["data"]["url"]

qrcode_image = qrcode.make(login_url)
qrcode_image.save("qrcode.png")

buffer = io.BytesIO()
qrcode_image.save(buffer, format="PNG")

base64_text = base64.b64encode(buffer.getvalue()).decode("ascii")
data_url = f"data:image/png;base64,{base64_text}"

print("二维码 Base64：")
print(data_url)

poll_url = (
    "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
)

while True:
    time.sleep(3)

    response = session.get(
        poll_url,
        params={
            "qrcode_key": qrcode_key,
            "source": "main-fe-header",
            "web_location": "333.1007",
            "x-bili-redirect": "1",
            "x-bili-locale-json": (
                '{"c_locale":{"language":"zh","script":"Hans"},'
                '"always_translate":true}'
            ),
            "x-bili-device-req-json": (
                '{"platform":"web","device":"pc","spmid":"333.1007",'
                '"mobi_app":"web_cn"}'
            ),
        },
    )

    payload = response.json()
    pprint(payload)

    data = payload["data"]

    if data["code"] == 0:
        # 访问 crossDomain，登录 Cookie 会自动写入 session.cookies
        session.get(data["url"])

        print("登录后的 Cookie：")
        pprint(session.cookies)

        nav = session.get(
            "https://api.bilibili.com/x/web-interface/nav"
        ).json()

        print("登录验证：")
        pprint(nav)
        break

    if data["code"] == 86038:
        print("二维码已失效")
        break