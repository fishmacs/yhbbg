#encoding=utf8

'''
Created on 2012-11-22

@author: zw
'''

##contants
USERTYPE_PARENT = 1
USERTYPE_STUDENT = 2
USERTYPE_TEACHER = 3
USERTYPE_SCHOOL_ADMIN = 4
USERTYPE_REGION_ADMIN = 5
USERTYPE_SYSTEM_ADMIN = 6

USER_TYPES = {
    USERTYPE_PARENT: ('parent', u'家长'),
    USERTYPE_STUDENT: ('student', u'学生'),
    USERTYPE_TEACHER: ('teacher', u'教师'),
    USERTYPE_SCHOOL_ADMIN: ('school admin', u'学校管理员'),
    USERTYPE_REGION_ADMIN: ('region admin', u'区域管理员'),
    USERTYPE_SYSTEM_ADMIN: ('sysadmin', u'系统管理员'),
}

USER_GENDERS = {'M': u'男', 'F':u'女'}

SCHOOLTYPE_ELEMENTARY = 1
SCHOOLTYPE_HIGH = 2
SCHOOLTYPE_JUNIOR_HIGH = 3
SCHOOLTYPE_SENIOR_HIGH = 4

SCHOOL_TYPES = {
    SCHOOLTYPE_ELEMENTARY: u'小学',
    SCHOOLTYPE_HIGH: u'中学',
    SCHOOLTYPE_JUNIOR_HIGH: u'初中',
    SCHOOLTYPE_SENIOR_HIGH: u'高中',
    }

SCHOOL_GRADES = [
    u'一年级', u'二年级', u'三年级', u'四年级', u'五年级', u'六年级',
    u'初一', u'初二', u'初三', u'高一', u'高二', u'高三',
]

PARENT_TYPE_FATHER = 0
PARENT_TYPE_MOTHER = 1
PARENT_TYPE_OTHER = 2
PARENT_TYPES = [u'父亲', u'母亲', u'其他']

COURSEWARE_STATE_WAITING = 0
COURSEWARE_STATE_CONVERTING = 1
COURSEWARE_STATE_CONVERTED = 10
#COURSEWARE_STATE_CONFIRMED = 20
COURSEWARE_STATE_DELIVERING = 30
COURSEWARE_STATE_FINISHED = 40
COURSEWARE_STATE_CONVERT_ERROR = -1
COURSEWARE_STATE_DELIVER_ERROR = -2

WARE_STATE_DESC = {
    COURSEWARE_STATE_WAITING: u'等待处理...',
    COURSEWARE_STATE_CONVERTING: u'格式转换中...',
    COURSEWARE_STATE_CONVERTED: u'格式转换完成',
#    COURSEWARE_STATE_CONFIRMED: u'审查通过',
    COURSEWARE_STATE_DELIVERING: u'分发中',
    COURSEWARE_STATE_FINISHED: u'分发完成',
    COURSEWARE_STATE_CONVERT_ERROR: u'转换出错，请重新上载',
    COURSEWARE_STATE_DELIVER_ERROR: u'分发出错，请重新分发'  
}

COURSEWARE_IMAGE_SIZE = (236, 336)

COURSE_IMAGE_SIZE = (140, 200)

SHARE_LEVEL_PRIVATE = 1
SHARE_LEVEL_CLASS_TYPE = 2
SHARE_LEVEL_GRADE = 3
SHARE_LEVEL_SCHOOL = 4
SHARE_LEVEL_REGION = 5
SHARE_LEVEL_PUBLIC = 6

SHARE_LEVELS = (
    (SHARE_LEVEL_PRIVATE, u'私有'),
    #(SHARE_LEVEL_CLASS_TYPE, u'班级类共享'),
    (SHARE_LEVEL_GRADE, u'年级共享'),
    (SHARE_LEVEL_SCHOOL, u'学校共享'),
    (SHARE_LEVEL_REGION, u'地区共享'),
    (SHARE_LEVEL_PUBLIC, u'公开'),
)

## functions
def get_grade_display(grade):
    return SCHOOL_GRADES[grade-1]

def get_all_grades(school_type, prompt=False):
    ret = prompt and [(0, u'请选择年级')] or []
    if school_type == SCHOOLTYPE_ELEMENTARY:
        i,j = 0,6
    elif school_type == SCHOOLTYPE_HIGH:
        i,j = 6,12
    elif school_type == SCHOOLTYPE_JUNIOR_HIGH:
        i,j = 6,9
    elif school_type == SCHOOLTYPE_SENIOR_HIGH:
        i,j = 9,12
    else:
        i,j = 0,0
    for g,n in enumerate(SCHOOL_GRADES[i:j]):
        ret.append((g+1+i, n))
    return ret

def get_all_schooltypes():
    types = SCHOOL_TYPES.items()
    types = sorted(types, key=lambda x: x[0])
    types.insert(0, (0, '--请选择类型--'))
    return types
