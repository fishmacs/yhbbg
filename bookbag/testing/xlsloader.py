#encoding=utf-8

import sys
import json

import xlrd

#from django.db.transaction import commit_on_success

from models import Test


def get_str(x, t):
    if t == 0:
        return ''
    if t == 1:
        return x.strip()
    elif t == 2:
        return str(int(x))
    raise Exception('类型不正确')
    
    
def get_int(x, t):
    if t == 0:
        return 0
    elif t == 1:
        return int(x)
    elif t == 2:
        return int(x)
    raise Exception('类型不正确')
    

def convert_int(a):
    try:
        return int(a)
    except:
        if len(a) == 1:
            i = ord(a)
            if 97 <= i <= 122:
                return i - 96
            elif 65 <= i <= 90:
                return i - 64
        raise Exception('答案格式不正确（只能为1,2,3,4或ABCD）')

        
def read_row(sheet, i):
    lst = sheet.row_values(i)
    section, title, type, num, answer, page, grid, hint = lst
    types = sheet.row_types(i)
    section = get_str(section, types[0])
    title = get_str(title, types[1])
    num = get_int(num, types[3])
    page = get_int(page, types[5])
    grid = get_int(grid, types[6])
    hint = get_str(hint, types[7])
    
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
    elif type == u'主观题':
        type = 'fm'
    elif type == u'是非':
        type = 'p'
        num = 2
    else:
        raise Exception('题目类型不正确')

    if type in ('ss', 'sm'):
        answer = [convert_int(s) for s in answer]
        
    return section, title, type, num, answer, page, grid, hint
    

#@commit_on_success
def load(filename, cid):
    wb = xlrd.open_workbook(filename)
    for sheet in wb.sheets():
        for i in xrange(1, sheet.nrows):
            try:
                section, title, type, num, answer, page, grid, hint = read_row(sheet, i)
                section = ' '.join([sheet.name, section])
                answer = json.dumps(answer, ensure_ascii=False)
                Test.objects.create(courseware_id=cid, section=section,
                                    title=title, seq=i,
                                    type=type, num=num, answer=answer,
                                    page=page, grid=grid, hint=hint)
            except Exception as e:
                _, e, tb = sys.exc_info()
                e = Exception('%s 第 %d 行：%s' % (sheet.name.encode('utf8'), i + 1, e))
                raise e.__class__, e, tb
