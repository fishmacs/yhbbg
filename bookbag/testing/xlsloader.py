#encoding=utf-8

import sys
import json

import xlrd

#from django.db.transaction import commit_on_success

from models import Test


def get_str(x, t):
    if t == 1:
        return x.strip()
    elif t == 2:
        return str(int(x))
    raise Exception('标题不正确')
    
    
def get_int(x, t):
    if t == 0:
        return 0
    elif t == 2:
        return int(x)
    raise Exception('选项个数不正确')
    

def read_row(sheet, i):
    lst = sheet.row_values(i)
    section, title, type, num, answer = lst
    types = sheet.row_types(i)
    section = get_str(section, types[0])
    title = get_str(title, types[1])
    num = get_int(num, types[3])
    
    answertype = types[4]
    if answertype == 0:
        answer = []
    elif answertype == 1:
        answer = answer.strip().split(',')
    elif answertype == 2:
        answer = [answer]

    type = type.strip()
    if type == u'单选':
        type = 'ss'
    elif type == u'多选':
        type = 'sm'
    elif type == u'填空':
        if answer:
            type = 'fk'
        else:
            type = 'fm'
    elif type == u'是非':
        type = 'p'
        num = 2
    else:
        raise Exception('题目类型不正确')
    
    return section, title, type, num, answer
    

#@commit_on_success
def load(filename, cid):
    wb = xlrd.open_workbook(filename)
    sheet = wb.sheets()[0]
    for i in xrange(1, sheet.nrows):
        try:
            section, title, type, num, answer = read_row(sheet, i)
            answer = json.dumps(answer, ensure_ascii=False)
            Test.objects.create(courseware_id=cid, section=section, seq=i,
                                type=type, num=num, answer=answer)
        except Exception as e:
            _, e, tb = sys.exc_info()
            e = Exception('第 %d 行：%s' % (i + 1, e))
            raise e.__class__, e, tb
