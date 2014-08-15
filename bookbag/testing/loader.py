import csv
import json

from chardet.universaldetector import UniversalDetector

from django.db.transaction import commit_on_success

from models import Test


def detect_encoding(f):
    d = UniversalDetector()
    line = f.readline()
    while(line):
        d.feed(line)
        if d.done:
            break
        line = f.readline()
    result = d.close()
    if result['confidence'] < 0.95:
        return 'gb18030'
    enc = result['encoding']
    return enc == 'gb2312' and 'gb18030' or enc


def decode(file, encoding):
    for line in file:
        try:
            yield line.decode(encoding)
        except UnicodeDecodeError:
            yield '???'


@commit_on_success
def import_csv(file):
    encoding = detect_encoding(file)
    file.seek(0)
    reader = csv.reader(decode(file, encoding))
    i, j = 1, 1
    curr_cid = None
    for row in reader:
        cid, section, title, type, num, answer = [field for field in row]
        try:
            json.loads(answer)
        except:
            raise Exception(u'第 %d 行：答案格式不正确' % i)
        if curr_cid != cid:
            j = 1
            curr_cid = cid
        else:
            j += 1
        Test.objects.create(courseware_id=cid, section=section, seq=j,
                            type=type, num=num, answer=answer)

        i += 1
        