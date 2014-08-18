#encoding=utf-8

import csv
import json

from chardet.universaldetector import UniversalDetector

from django.db.transaction import commit_on_success

from models import Test


def detect_encoding(f):
    d = UniversalDetector()
    buf = f.read(2048)
    while(buf):
        d.feed(buf)
        if d.done:
            break
        buf = f.read(2048)
    result = d.close()
    # if result['confidence'] < 0.95:
    #     return 'gb18030'
    enc = result['encoding']
    return enc == 'gb2312' and 'gb18030' or enc


def decode(s, encoding):
    try:
        return s.decode(encoding)
    except UnicodeDecodeError:
        return '???'


@commit_on_success
def import_csv(file):
    #csv.field_size_limit(6)
    encoding = detect_encoding(file)
    #dialect = csv.Sniffer().sniff(file.read(1024))
    file.seek(0)
    reader = csv.reader(file)
    i, j = 1, 1
    curr_cid = None
    for row in reader:
        cid, section, title, type, num, answer = [decode(field.strip(), encoding) for field in row]
        if answer:
            alist = answer.split('|')
            alist = [s.replace('%7C', '|').replace('%2C', ',') for s in alist]
        else:
            alist = []
        if type == 'single':
            type = 'ss'
        elif type == 'multiple':
            type = 'sm'
        elif type == 'input':
            if alist:
                type = 'fk'
            else:
                type = 'fm'
        else:
            raise Exception(u'第 %d 行：题目类型不正确' % i)
        if curr_cid != cid:
            j = 1
            curr_cid = cid
        else:
            j += 1
        answer = json.dumps(alist, ensure_ascii=False)
        Test.objects.create(courseware_id=cid, section=section, seq=j,
                            type=type, num=num, answer=answer)
        i += 1
        