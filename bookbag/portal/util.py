'''
Created on 2012-12-11

@author: zw
'''

import os
import numpy
import tempfile
import gzip

from datetime import date, datetime

import models

### encode mrf while converting, and decode while deliver
BUFFER_SIZE = 32 * 1024


def guess_semester_start():
    today = date.today()
    start1 = date(today.year-1, 9, 1)
    start2 = date(today.year, 2, 20)
    start3 = date(today.year, 9, 1)
    if today >= start3:
        return start3
    elif today < start2:
        return start1
    return start2


def weeks_of_semester(date, semester_start):
    wd_start = semester_start.weekday()
    td = date - semester_start
    return (td.days+wd_start+6) / 7


def calc_grade(year, start_date):
    now = date.today()
    grade = now.year - year + 1
    if grade > 0 and now < date(now.year, start_date.month, start_date.day):
        grade -= 1
    return grade


def fill_key(encode_key, size):
    n = size / len(encode_key)
    s = size % len(encode_key)
    keys0 = [c for c in encode_key]
    keys = []
    for i in xrange(n):
        keys += keys0
    for i in xrange(s):
        keys.append(encode_key[i])
    return numpy.frombuffer(''.join(keys), dtype=numpy.byte)


def encode_file(infile, outfile):
    f0 = open(infile, 'rb')
    f1 = open(outfile, 'wb')
    keys = fill_key('hongkou188', BUFFER_SIZE)
    try:
        s = f0.read(BUFFER_SIZE)
        while s:
            l = len(s)
            f1.write(encode(s, keys if l == len(keys) else keys[:l]))
            s = f0.read(BUFFER_SIZE)
    finally:
        f0.close()
        f1.close()


def encode(s, keys):
    a = numpy.bitwise_xor(numpy.frombuffer(s, dtype=numpy.byte), keys)
    return a.tostring()


def pdf_from_mrf(cid, mrf):
    try:
        tmp = models.TempFile.objects.get(type='courseware', obj_id=cid)
    except:
        f, tmpfile = tempfile.mkstemp('.pdf')
        os.close(f)
        encode_file(mrf, tmpfile)
        tmp = models.TempFile.objects.create(type='courseware', obj_id=cid,
                                             path=tmpfile)
    else:
        if not os.path.exists(tmp.path) or \
           os.path.getmtime(tmp.path) < os.path.getmtime(mrf):
            encode_file(mrf, tmp.path)
            tmp.modified_time = datetime.now()
            tmp.save()
    return tmp.path


def get_uploaded_tmpfile(file):
    return gzip.GzipFile(fileobj=file, mode='rb')
