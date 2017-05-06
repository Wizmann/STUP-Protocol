#!/usr/bin/python

from StupPacket import *

from AckPacket import *
from SynPacket import *
from SynAckPacket import *
from FinPacket import *
from RstPacket import *
from LivPacket import *
from LivAckPacket import *

def serialize(packet):
    return Packet.serialize(packet)

def deserialize(data):
    return Packet.deserialize(data)
