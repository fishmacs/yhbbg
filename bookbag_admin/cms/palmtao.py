import sys
import os
import struct
from datetime import datetime
from Crypto.PublicKey import RSA as rsa
from Crypto.Hash import MD5 as md5

LICENSE_FILE = '/var/www/bupt/license.dat'
CEIBS_KEY = '/var/www/bupt/ceibs.key'
PALMTAO_KEY = '/var/www/bupt/palmtao.key'
DELIMETER = '\x00'*16

class LicenseExpiredError(Exception): pass
class LicenseInvalidError(Exception): pass
class LicenseNotFoundError(Exception): pass

class KeyFileNotFoundError(Exception): pass

# for control-flow in views.py
class LicenseException(Exception): pass

def read_key_file(filename):
    f = open(filename)
    s = f.read()
    f.close()
    return s

def check_license():
    if not os.path.exists(LICENSE_FILE):
        raise LicenseNotFoundError()
    if not os.path.exists(CEIBS_KEY) or not os.path.exists(PALMTAO_KEY):
        raise KeyFileNotFoundError()
    
    f = open(LICENSE_FILE, 'rb')
    try:
        encrypted, signature = f.read().split(DELIMETER)
        k = rsa.importKey(read_key_file(CEIBS_KEY))
        # encrypt to get date string
        decrypted = k.decrypt((encrypted,))
        d = datetime.strptime(decrypted, '%Y-%m-%d')
    except ValueError:
        raise LicenseInvalidError()
    
    now = datetime.now()
    if d < now:
        raise LicenseExpiredError()
    # verify signature
    s = 0L
    for x in signature[::-1]:
        s = (s<<8L) + ord(x)
    k = rsa.importKey(read_key_file(PALMTAO_KEY))
    h = md5.new(decrypted).digest()
    if not k.verify(h, (s,)):
        raise LicenseInvalidError()
    # return remained days
    delta = d - now
    return delta.days

