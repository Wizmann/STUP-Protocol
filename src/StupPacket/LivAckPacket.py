#!/usr/bin/python
from .StupPacket import Packet

class LivAckPacket(Packet):
    def __init__(self, ack_number, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.liv = 1
        self.ack = 1
        self.ack_number = ack_number
