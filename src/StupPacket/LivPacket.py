#!/usr/bin/python
from .StupPacket import Packet

class LivPacket(Packet):
    def __init__(self, seq_number, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)
        self.liv = 1
        self.seq_number = seq_number
