#coding=utf-8
import json
import requests
import gevent

from gevent import monkey
monkey.patch_all()

URL = 'http://localhost:8000/'

def download(url):
    l = len(requests.get(url).text)
    return l

if __name__ == '__main__':
    r = requests.get(URL)

    pool = gevent.pool.Pool(5)

    urls = [ URL + item for item in r.json() ]
    for url in urls:
        pool.spawn(download, url)
    pool.join()

