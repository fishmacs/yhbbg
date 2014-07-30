#encoding=utf-8

from django.core.cache import cache

import db_util

def get_grade_classes(school, grade, prompt=True):
    classes = get_cached_object(
        'school__%d:grade__%d:classes' %(school, grade),
        lambda: db_util.classes_of_grade(school, grade))
    if prompt:
        classes.insert(0, (0, u'请选择班级'))
    return classes

def clear_grade_classes(school, grade):
    cache.delete('school__%d:grade__%d:classes' %(school, grade))
    
def get_grade_courses(region, school, grade):
    return get_cached_object(
        'school__%d:grade__%d:courses' %(school, grade),
        lambda: db_util.courses_of_grade(region, school, grade))

def clear_grade_courses(region, school, grade):
    cache.delete('school__%d:grade__%d:courses' %(school, grade))
    
def get_all_regions(prompt=True):
    def dbfunc():
        regions = db_util.get_all_regions()
        return [(r.id, r.name) for r in regions]
    regions = get_cached_object('all_regions', dbfunc)
    if prompt:
        regions.insert(0, (0, u'请选择地区'))
    return regions

def clear_all_regions():
    cache.delete('all_regions')
    
def get_region_schools(region, prompt=True):
    def dbfunc():
        schools = db_util.search_school(region)
        return [(s.id, s.name) for s in schools]
    schools = get_cached_object(
        'region__%d:search__:search_type__name:schools' % region,
        dbfunc)
    if prompt:
        schools.insert(0, (0, u'请选择学校'))
    return schools

def clear_region_schools(region):
    cache.delete('region__%d:search__:search_type__name:schools' % region)
    
def search_school(region, search, search_type):
    return get_cached_object(
        'region__%s:search__%s:search_type__%s:schools' %(region, search is not None and search or '', search_type is not None and search_type or ''), 
        lambda: db_util.search_school(region, search, search_type))

        
def get_cached_object(key, getfunc):
    obj = cache.get(key)
    if not obj:
        obj = getfunc()
        cache.set(key, obj)
    return obj

    
def get_selected_grade(user, key):
    k = 'user__%s:%s:grade' % (user.username, key)
    return cache.get(k, 0)

def set_selected_grade(user, key, grade, timeout=None):
    k = 'user__%s:%s:grade' % (user.username, key)
    cache.set(k, grade, timeout)


def get_selected_schooltype(user, key):
    k = 'user__%s:%s:school_type' % (user.username, key)
    return cache.get(k, 0)

def set_selected_schooltype(user, key, school_type, timeout=None):
    k = 'user__%s:%s:school_type' % (user.username, key)
    cache.set(k, school_type, timeout)
