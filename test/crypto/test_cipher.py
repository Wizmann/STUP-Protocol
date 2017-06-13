#coding=utf-8
import os
import sys
import unittest

from stup.crypto.cipher import *

class TestAESCrypto(unittest.TestCase):
    def test_padding(self):
        assert padding(len("foo"), 1, 3 )[1]  == 3
        assert padding(len("foo"), 3, 3 )[1]  == 3
        assert padding(len("foo"), 16, 3)[1]  == 13
        assert padding(len("foo"), 2, 3 )[1]  == 3

    def test_aes_ecb(self):
        key = "she's me before I grew into myself and got hotter with age."
        aes1 = AESCrypto_ECB(key)
        aes2 = AESCrypto_ECB(key)

        messages = [
            "I just... You have no idea how I've longed to hear those words.",
            "I...",
            "I forgive you. Can you forgive...",
            "You're being sarcastic.",
            "Oh, how you know me.",
        ]

        for message in messages:
            padding, padding_length = \
                    aes1.padding(len(message), random.randint(1, 12))
            a = aes1.encrypt(message.encode('UTF-8') + padding)
            assert len(a) == len(message.encode('UTF-8') + padding)

            b = aes2.decrypt(a)
            assert b[:-padding_length] == message.encode('UTF-8')

class TestAESCrypto_with_IV(unittest.TestCase):
    def test_aes_ecb(self):
        iv = b"fk"
        key = "she's me before I grew into myself and got hotter with age."
        aes1 = AESCrypto_ECB_with_IV(key)
        aes2 = AESCrypto_ECB_with_IV(key)

        messages = [
            "I just... You have no idea how I've longed to hear those words.",
            "I...",
            "I forgive you. Can you forgive...",
            "You're being sarcastic.",
            "Oh, how you know me.",
        ]

        for message in messages:
            padding, padding_length = \
                    aes1.padding(len(message), random.randint(1, 12))
            a = aes1.encrypt(iv, message.encode('UTF-8') + padding)
            assert len(a) == len(message.encode('UTF-8') + padding)

            b = aes2.decrypt(iv, a)
            assert b[:-padding_length] == message.encode('UTF-8')
