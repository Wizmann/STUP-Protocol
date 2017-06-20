#coding=utf-8
import json
import os
import random
import six

import bottle

if six.PY2:
    from six.moves import xrange as range

TMPFILES = []

def gen_tmp_file(l, r, step):
    file_size = l
    while file_size <= r:
        fn = '%d.tmp' % file_size
        TMPFILES.append(fn)
        file_size += step

        if os.path.exists(fn):
            continue

        with open(fn, 'w') as tmpfile:
            for _ in range(file_size):
                tmpfile.write(chr(random.randint(0, 255)))

@bottle.route('/')
def index():
    return json.dumps(TMPFILES)

@bottle.route('/<name>')
def getfile(name):
    with open(name, 'r') as tmpfile:
        return tmpfile.read()

if __name__ == '__main__':
    gen_tmp_file(50, 2 * 1024, 50)
    gen_tmp_file(2 * 1024, 50 * 1024, 512)

    bottle.run(host='localhost', port=8000)
