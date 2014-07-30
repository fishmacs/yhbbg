#encoding=utf-8

import sys
import os
from datetime import date

from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.utils.http import urlquote

#from tastypie.models import ApiKey

import image
import global_def


class Region(models.Model):
    name = models.CharField(unique=True, max_length=16, verbose_name=u'所在地区')
    code = models.CharField(unique=True, max_length=10, verbose_name=u'地区代码')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'region'

    def __unicode__(self):
        return self.name


class School(models.Model):
    name = models.CharField(unique=True, max_length=80, verbose_name=u'学校名称')
    code = models.CharField(unique=True, max_length=20, verbose_name=u'学校代码')
    type = models.SmallIntegerField(verbose_name=u'学校类型', choices=global_def.get_all_schooltypes())
    description = models.CharField(max_length=200, verbose_name=u'学校介绍', default='', blank=True)
    region = models.ForeignKey(Region, verbose_name=u'所在地区')
    region_name = models.CharField(max_length=16)
    address = models.CharField(max_length=80, verbose_name=u'地址', default='', blank=True)
    telphone = models.CharField(max_length=20, verbose_name=u'电话', default='', blank=True)
    email = models.EmailField(max_length=40, verbose_name=u'电子邮件', default='', blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'school'

    def __unicode__(self):
        return self.name

    def get_type(self):
        return global_def.SCHOOL_TYPES[self.type]

    
class Semester(models.Model):
    region = models.ForeignKey(Region, blank=True, null=True)
    school = models.ForeignKey(School, blank=True, null=True)
    grade = models.SmallIntegerField(blank=True, null=True)
    name = models.CharField(verbose_name=u'名称', max_length=20)
    start_date = models.DateField(verbose_name=u'开始日期')
    end_date = models.DateField(verbose_name=u'结束日期')
    
    class Meta:
        db_table = 'semester'

    def __unicode__(self):
        return self.name

    
class ClassType(models.Model):
    name = models.CharField(unique=True, max_length=16, verbose_name=u'班级类型')
    
    class Meta:
        db_table = 'class_type'


class SchoolGradeClasstype(models.Model):
    school = models.ForeignKey(School, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    class_type = models.ForeignKey(ClassType)

    class Meta:
        db_table = 'school_grade_classtype'

        
#school-class crosss link
class SchoolClass(models.Model):
    name = models.CharField(max_length=80, verbose_name=u'班级名称')
    year = models.IntegerField(default=2012)
    start_date = models.DateField(verbose_name=u'入学日期')
    end_date = models.DateField(verbose_name=u'毕业日期')
    class_type = models.ForeignKey(ClassType, null=True)
    school = models.ForeignKey(School)
    is_active = models.BooleanField(default=True)
    
    def get_grade(self):
        now = date.today()
        grade = now.year - self.year + 1
        if grade > 0 and now < date(now.year, self.start_date.month, self.start_date.day):
            grade -= 1
        return grade

    def get_grade_display(self):
        return global_def.get_grade_display(self.get_grade())

    def get_name(self):
        return self.get_grade_display() + self.name
    
    class Meta:
        db_table = 'school_class'
        

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    usertype = models.SmallIntegerField(default=global_def.USERTYPE_STUDENT)
    region = models.ForeignKey(Region, blank=True, null=True)
    school = models.ForeignKey(School, blank=True, null=True)
    myclass = models.ForeignKey(SchoolClass, blank=True, null=True)
    parents = models.ManyToManyField("self", related_name='children', symmetrical=False)
    gender = models.CharField(max_length=1)
    student_id = models.CharField(max_length=20, default='')
    telphone = models.CharField(max_length=20, default='')
    birthday = models.DateField(blank=True, null=True)
    address = models.CharField(max_length=80, default='')
    contact = models.TextField(blank=True, null=True)
    device_id = models.CharField(max_length=32, default='', db_index=True)
    #mac_addr = models.CharField(max_length=20, default='')
    #serial_no = models.CharField(max_length=48, default='')
    newware_count = models.IntegerField(default=0)
    app_version = models.CharField(max_length=20, default='')
    
    class Meta:
        db_table = 'userprofile'

    def get_usertype(self):
        return global_def.USER_TYPES[self.usertype][0]

    def get_usertype_display(self):
        return global_def.USER_TYPES[self.usertype][1]
        
    def get_gender(self):
        return global_def.USER_GENDERS.get(self.gender, '')

    def get_age(self):
        if not self.birthday:
            return None
        now = date.today()
        age = now.year - self.birthday.year
        if self.birthday > date(self.birthday.year, now.month, now.day):
            age -= 1
        return age

        
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        #ApiKey.objects.create(user=instance)
        
# multiple imports causes mutlple registers and multiple creation of userprofile, resolve with displath_uid argument
post_save.connect(create_user_profile, sender=User, dispatch_uid='bookbag.common.models')


class Parent(models.Model):
    child = models.ForeignKey(User)
    name = models.CharField(max_length=16)
    relation = models.SmallIntegerField(default=0)
    contact = models.TextField(default='')

    class Meta:
        db_table = 'parent'


## misc configuration data
class MiscConfig(models.Model):
    conf_key = models.CharField(primary_key=True, max_length=30)
    conf_val = models.CharField(max_length=80, default=settings.DEFAULT_OFFLINE_TIMEOUT)

    class Meta:
        db_table = 'misc_conf'

    def __unicode__(self):
        return self.conf_key


fs = FileSystemStorage(location=settings.COURSEWARE_UPLOAD_DIR)


class Course(models.Model):
    cid = models.CharField(unique=True, max_length=80, verbose_name=u'课程代码')
    course_name = models.CharField(max_length=80, verbose_name=u'课程名称')
    english_name = models.CharField(max_length=80, default='', blank=True, verbose_name=u'英文名称')
    image = models.ImageField(storage=fs, upload_to='images/courses',
                              default=settings.DEFAULT_COURSE_IMAGE.replace(settings.MEDIA_URL, ''),
                              blank=True, verbose_name=u'图片')
    description = models.CharField(max_length=200, default='', blank=True, verbose_name=u'描述')
    
    class Meta:
        db_table = 'course'

    def __unicode__(self):
        return self.course_name

    def get_image_url(self):
        try:
            image.prepare_image(self.image, global_def.COURSE_IMAGE_SIZE)
            return self.image.url
        except Exception, e:
            print >>sys.stderr, e
            return settings.DEFAULT_COURSE_IMAGE


# grade-course cross link
class GradeCourse(models.Model):
    # school_id/class_id: 少数特殊课程可能只属于某个学校或某个班级
    school = models.ForeignKey(School, blank=True, null=True)
    class_type = models.ForeignKey(ClassType, blank=True, null=True)
    grade = models.SmallIntegerField(blank=True, null=True)
    course = models.ForeignKey(Course)
    semester = models.SmallIntegerField(blank=True, null=True)
    
    class Meta:
        db_table = 'grade_course'
        

# teach-class-course cross link
class TeacherClassCourse(models.Model):
    teacher = models.ForeignKey(User)
    myclass = models.ForeignKey(SchoolClass)
    course = models.ForeignKey(Course)

    class Meta:
        db_table = 'teacher_class_course'
        unique_together = ('teacher', 'myclass', 'course')
        
    
# 教材版本
class BookProvider(models.Model):
    name = models.CharField(max_length=40)
    name_en = models.CharField(max_length=40, default='')
    
    class Meta:
        db_table = 'book_provider'
 

class CoursewareCategory(models.Model):
    name_ch = models.CharField(max_length=16)
    name_en = models.CharField(max_length=16)
    
    class Meta:
        db_table = 'courseware_category'


class Courseware(models.Model):
    name = models.CharField(max_length=80)
    book_provider = models.ForeignKey(BookProvider)
    #category = models.IntegerField(choices=db_util.get_courseware_categories())
    category = models.ForeignKey(CoursewareCategory)
    course = models.ForeignKey(Course)
    class_type = models.ForeignKey(ClassType, blank=True, null=True)
    classes = models.ManyToManyField(SchoolClass, related_name='coursewares')
    teacher = models.ForeignKey(User)
    grade = models.SmallIntegerField()
    week = models.SmallIntegerField()
    volume_id = models.CharField(max_length=32)
    description = models.CharField(max_length=200, default='')
    state = models.SmallIntegerField()
    path = models.CharField(max_length=128)
    image = models.ImageField(storage=fs, upload_to='images/coursewares',
                              default=settings.DEFAULT_COURSEWARE_IMAGE.replace(settings.MEDIA_URL, ''))
    outpath = models.CharField(max_length=128)
    errmsg = models.CharField(max_length=80, default='')
    share_level = models.SmallIntegerField()
    password = models.CharField(max_length=20, default='')
    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'courseware'
        
    def __unicode__(self):
        return self.name

    def state_str(self):
        return global_def.WARE_STATE_DESC[self.state]

    def is_converted(self):
        return self.state >= global_def.COURSEWARE_STATE_CONVERTED or \
            self.state == global_def.COURSEWARE_STATE_DELIVER_ERROR

    def reconvertable(self):
        if self.is_converted():
            _, ext = os.path.splitext(self.path)
            return ext.lower() == '.pdf'
        return False
        
    def next_action(self):
        if self.state == global_def.COURSEWARE_STATE_WAITING:
            return (u'开始格式转换', '/courseware/convert/%d/' % self.id)
        elif self.state == global_def.COURSEWARE_STATE_CONVERTED:
            return (u'分发', '/courseware/deliver/%d/' % self.id)
        elif self.state == global_def.COURSEWARE_STATE_FINISHED:
            return (u'取消分发', '/courseware/undeliver/%d/' % self.id)
        elif self.state == global_def.COURSEWARE_STATE_CONVERT_ERROR:
            return (u'重新转换', '/courseware/convert/%d/' % self.id)
        elif self.state == global_def.COURSEWARE_STATE_DELIVER_ERROR:
            return (u'重新分发', '/courseware/deliver/%d/' % self.id)
        # elif self.state == COURSEWARE_STATE_DELIVERING or  \
        #      self.state == COURSEWARE_STATE_FINISHED:
        #     return [(u'下载', self.get_absolute_url())]
        elif self.state in (global_def.COURSEWARE_STATE_CONVERTING, global_def.COURSEWARE_STATE_DELIVERING):
            return '', settings.STATIC_URL + 'images/loading.gif'
        else:
            return None

    def get_absolute_url(self):
        # return '%s?coursename=%s&courseid=%d&bookname=%s&bookid=%d&category=%s&type=mrf&password=%s' \
        #        %(settings.BASE_DOWNLOAD_URL, urlquote(self.course_name),
        #          self.courseid, urlquote(self.name), self.id, self.category,
        #          urlquote(self.password.encode('utf8')))
        return '%s?bookid=%d&password=%s&type=mrf' \
               % (settings.BASE_DOWNLOAD_URL, self.id, urlquote(self.password.encode('utf8')))

    def get_download_url(self):
        return settings.BASE_DOWNLOAD_URL + '?'

    def get_image_url(self):
        try:
            image.prepare_image(self.image, global_def.COURSEWARE_IMAGE_SIZE)
            return self.image.url
        except Exception, e:
            print >>sys.stderr, e
            return settings.DEFAULT_COURSEWARE_IMAGE


class UserCourseware(models.Model):
    user = models.ForeignKey(User)
    #url = models.URLField(verify_exists=False)
    url = models.CharField(max_length=128, default='')
    raw = models.ForeignKey(Courseware)
    created_time = models.DateTimeField(auto_now_add=True)
    download_time = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'user_courseware'
        unique_together = ('user', 'raw',)
        
    def __unicode__(self):
        return self.raw.name


class UserAnyDevice(models.Model):
    user = models.ForeignKey(User)

    class Meta:
        db_table = 'user_any_device'


class CourseSchedule(models.Model):
    myclass = models.ForeignKey(SchoolClass)
    weekday = models.SmallIntegerField()
    courses = models.CommaSeparatedIntegerField(max_length=40)

    class Meta:
        db_table = 'course_schedule'

        
class SchoolContacts(models.Model):
    school = models.ForeignKey(School)
    person = models.ForeignKey(User, blank=True, null=True)
    person_name = models.CharField(max_length=16)
    contact = models.TextField()

    class Meta:
        db_table = 'school_contacts'

        
class ClassContacts(models.Model):
    myclass = models.ForeignKey(SchoolClass)
    person = models.ForeignKey(User, blank=True, null=True)
    person_name = models.CharField(max_length=16)
    contact = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'class_contacts'


# class InformMessage(models.Model):
#     user = models.ForeignKey(User)
#     message = models.CharField(max_length=200, default='')
#     time = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         db_table = 'inform_message'


# MSG_STATE_INIT = 0
# MSG_STATE_PUSHED = 1
# MSG_STATE_PUSH_ERROR = -1

# class MessageUsers(models.Model):
#     message = models.ForeignKey(InformMessage)
#     user = models.ForeignKey(User)
#     cls = models.ForeignKey(StuClass, null=True)
#     state = models.SmallIntegerField(default=MSG_STATE_INIT)
    
#     class Meta:
#         db_table = 'message_users'
#         unique_together = ('message', 'user')
