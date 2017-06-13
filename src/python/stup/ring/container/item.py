#coding=utf-8
from .. import Utils

class ContainerItem(object):
    def __init__(self, range_l, range_r, payload):
        self.range_l = Utils.to_u32(range_l)
        self.range_r = Utils.to_u32(range_r)
        self.payload = payload

    def size(self):
        return Utils.seq_sub(self.range_r, self.range_l)

    def __str__(self):
        return '[%d %d] %s' \
            % (self.range_l, self.range_r, self.payload)

