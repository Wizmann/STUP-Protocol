#!/usr/bin/python
from .StupPacket import Packet

class SynAckPacket(Packet):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.syn = 1
        self.ack = 1
