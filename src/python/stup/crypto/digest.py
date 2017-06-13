from __future__ import absolute_import, print_function, with_statement

import Crypto.Hash.MD5

def digest(plain_text):
    return Crypto.Hash.MD5.new(plain_text.encode('UTF-8')).digest()
