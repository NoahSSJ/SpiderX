import pickle
from pprint import pprint
import sqlite3
from crawl import XhsSpider
from pathlib import Path

# def run():
#     a = XhsSpider()
    # a.process_urls()
    # url = next(a.consume_urls())
    # # print(url)
    # # url = 'https://www.xiaohongshu.com/explore/6ab24f1b000000003003fa95?xsec_token=ABpmmRU_-yRTWoo9pF9gwBkdsnC209P8_AwkJAzAwCkns=&xsec_source=pc_feed'
    # kwargs = next(a.parse_url(url))
    # pprint(kwargs)
    # title = kwargs['title']
    # image_list = kwargs['image_list']
    # video_list = kwargs['video_list']

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

def run():
    db_path = Path(__file__).joinpath('xhs.db')
    conn = sqlite3.connect('xhs.db')
    sql_str = """
        CREATE TABLE IF NOT EXISTS wk(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            uid TEXT NOT NULL,
            title TEXT NOT NULL,
            image_list BLOB NOT NULL,
            video_list BLOB NOT NULL
        )
    """
    conn.execute(sql_str)
    a = XhsSpider()
    uid = a.uid
    name = a.name
    a.process_urls()
    for index, url in enumerate(a.consume_urls(), start=1):
        kwargs = next(a.parse_url(url))
        title = kwargs['title']
        image_list = kwargs['image_list']
        video_list = kwargs['video_list']
        sql = "INSERT OR IGNORE INTO wk (name, uid, title, image_list, video_list) values (?, ?, ?, ?, ?)"
        conn.execute(sql, (name, uid, title, pickle.dumps(image_list), pickle.dumps(video_list)))
    conn.commit()



run()