#!/usr/bin/python
import random
import string
import md5
import datetime
import time
import string
import logging

from twisted.python import log

'''
observer = log.PythonLoggingObserver()
observer.start()
'''

fmt = "%(levelname)-8s %(asctime)-15s [%(filename)s:%(lineno)d] %(message)s"
logging.basicConfig(format=fmt, level=logging.INFO)

UINT32_MIN = 0x00000000
UINT32_MAX = 0xFFFFFFFF

def rand_str(length):
    return ''.join([
        random.choice(string.ascii_letters + string.digits)
        for i in xrange(length)
    ])

def md5sum(s):
    return md5.new(s).digest()

def to_u32(value):
    return int(value) & UINT32_MAX

def is_u32(value):
    return UINT32_MIN <= value <= UINT32_MAX

def rand_u32():
    return random.randint(0, UINT32_MAX)

def datetime_str():
    return datetime.datetime.now().strftime('%Y%m%d.%H%M%S.%f')

def cur_second():
    return time.time()

def cur_millisecond():
    return second_to_millisecond(time.time())

def millisecond_to_second(ms):
    return 1.0 * ms / 1000

def second_to_millisecond(sec):
    return int(round(sec * 1000))

def seq_add(key, offset):
    return (key + offset + UINT32_MAX + 1) & UINT32_MAX

def seq_sub(key, offset):
    return (key - offset + UINT32_MAX + 1) & UINT32_MAX

def nop(*args, **kwargs):
    pass

# this code clip is from Python Cookbook, 2nd Edition(1.11)
# Credit: Andrew Dalke
text_characters = "".join(map(chr, range(32, 127))) + "\n\r\t\b"
_null_trans = string.maketrans("", "")
def istext(s, text_characters=text_characters, threshold=0.30):
    # if s contains any null, it's not text:
    if "\0" in s:
        return False
    # an "empty" string is "text" (arbitrary but reasonable choice):
    if not s:
        return True
    # Get the substring of s made up of non-text characters
    t = s.translate(_null_trans, text_characters)
    # s is 'text' if less than 30% of its characters are non-text ones:
    return 1.0 * len(t) / len(s) <= threshold

class TcpRttEstimator(object):
    ALPHA = 0.125
    BETA = 0.25
    MU = 1.0
    DELTA = 4.0
    def __init__(self):
        self.srtt = 0
        self.devrtt = 0
        
    def nextRTO(self, rtt):
        self.srtt += self.ALPHA * (rtt - self.srtt)
        self.devrtt = (1 - self.BETA) * self.devrtt + self.BETA * abs(rtt - self.srtt)
        rto = 1.0 * self.MU * self.srtt + self.DELTA * self.devrtt
        return rto
