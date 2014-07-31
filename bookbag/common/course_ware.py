import sys
import os
import time
from threading import Thread

#from django.conf import settings
from django.db.models import Q
import models
from models import Courseware, UserCourseware
import converter
import global_def
import util


def users_can_see_courseware(courseware):
    grade = courseware.grade
    year = util.get_grade_year(grade)
    qs = models.TeacherClassCourse.objects.filter(Q(teacher=courseware.teacher), Q(myclass__year=year),
                                                  course=courseware.course_id)
    ### it's courseware.class_type is null, not mycalss.class_type is null
    #Q(myclass__class_type__isnull=True)|Q(myclass__class_type=courseware.class_type),
    if courseware.class_type:
        qs = qs.filter(myclass__class_type=courseware.class_type)
    class_ids = [x.myclass_id for x in qs]
    return models.UserProfile.objects.filter(myclass_id__in=class_ids)

    
def create_courseware(course_id, grade, user, path, args):
    if not args['image']:
        image = Courseware._meta.get_field('image').default  # settings.DEFAULT_COURSEWARE_IMAGE.replace('/media/', '')
    courseware = Courseware.objects.create(
        name=args['title'],
        grade=grade,  # int(args['grade']),
        book_provider_id=int(args['provider']),
        category_id=int(args['category']),
        share_level=int(args['share']),
        week=int(args['week']),
        volume_id=args.get('volume_id', 'V0001'),
        description=args['description'],
        image=image,  # password=args['password'],
        state=global_def.COURSEWARE_STATE_WAITING,
        path=path, course_id=course_id, teacher=user)
    courseware.classes.add(*args['classes'])
    return courseware


def convert_courseware(courseware, reconvert, port):
    try:
        courseware.outpath = converter.convert_upload(
            courseware.id, courseware.teacher.id,
            str(courseware.course_id), courseware.path,
            reconvert, 'mrf_pdf', 7, port)
        courseware.state = global_def.COURSEWARE_STATE_CONVERTING
    except Exception, e:
        courseware.state = global_def.COURSEWARE_STATE_CONVERT_ERROR
        courseware.errmsg = str(e)[:80]
    courseware.save()


class DeliverThread(Thread):
    def __init__(self, courseware):
        Thread.__init__(self)
        self.courseware = courseware
        
    def run(self):
        #=======================================================================
        # push_dict = {}
        #=======================================================================
        for user in users_can_see_courseware(self.courseware):
            try:
                if deliver_user_courseware(user, self.courseware):
                    # user is userprofile
                    user.newware_count += 1
                    user.save()
                    
                    #===========================================================
                    # push_url = settings.PUSH_URL.get(user.app_version, '')
                    # if push_url:
                    #    try:
                    #        devices,badges,messages = push_dict[push_url] 
                    #    except KeyError:
                    #        devices = []
                    #        badges = []
                    #        messages = []
                    #        push_dict[push_url] = (devices, badges, messages)
                    #    devices.append(user.device_id)
                    #    badges.append(user.newware_count)
                    #    messages.append('')
                    #===========================================================
            except IOError, e:
                self.courseware.state = global_def.COURSEWARE_STATE_DELIVER_ERROR
                self.courseware.errmsg = str(e)
                self.courseware.save()
                return
            except:
                pass
            time.sleep(0.1)
        self.courseware.state = global_def.COURSEWARE_STATE_FINISHED
        self.courseware.save()
        #=======================================================================
        # push_update_messages(push_dict)
        #=======================================================================

        
def deliver_courseware(courseware):
    courseware.state = global_def.COURSEWARE_STATE_DELIVERING
    courseware.save()
    task = DeliverThread(courseware)
    task.start()


def undeliver_courseware(courseware):
    courseware.state = global_def.COURSEWARE_STATE_CONVERTED
    courseware.save()
    delete_delivered(courseware)

    
def deliver_user_courseware(user, courseware):
    print user.user_id, user.device_id
    if hasattr(user, 'device_id'):
        # user is profile
        device_id = user.device_id
        user_id = user.user_id
    else:
        device_id = user.userprofile.device_id
        user_id = user.id
    if device_id:
        already_delivered = get_already_delivered(courseware, user_id)
        if already_delivered and already_delivered.created_time > courseware.modified_time:
            return already_delivered
        already_delivered and already_delivered.delete()
        try:
            path = converter.deliver_file(
                courseware.id, user_id,
                courseware.outpath, device_id)
            finished = UserCourseware.objects.create(
                user_id=user_id, raw=courseware, url=path)
            return finished
        except Exception, e:
            print >>sys.stderr, 'deliver failed: ', e
    return None


def convert_finish(courseware_id, errmsg):
    courseware = Courseware.objects.get(pk=courseware_id)
    courseware.state = not errmsg and global_def.COURSEWARE_STATE_CONVERTED or global_def.COURSEWARE_STATE_CONVERT_ERROR
    courseware.errmsg = errmsg[:80]
    courseware.save()

# def deliver_finish(courseware_id, uid, path, errmsg):
#     courseware = Courseware.objects.get(pk=courseware_id)
#     user = User.objects.get(pk=uid)
#     if not errmsg:
#         finished = UserCourseware.objects.create(
#             user=user, raw=courseware, url=path)

    
def coursewares_of_course(course_id, grade, user=None):
    coursewares = Courseware.objects.select_related('category').filter(course=course_id, grade=grade)
    if user:
        coursewares = coursewares.filter(teacher=user)
    return coursewares

# def delete_coursewares(user):
#     for course in UserCourseware.objects.filter(user__exact=user):
#         try:
#             os.remove(course.url)#.encode('utf8'))
#         except OSError:
#             pass
#         finally:
#             course.delete()


def delete_courseware(courseware):
    delete_delivered(courseware)
    try:
        os.remove(courseware.outpath)
        os.remove(courseware.path)
    except OSError:
        pass
    finally:
        courseware.delete()


def delete_delivered(raw):
    for course in UserCourseware.objects.filter(raw=raw):
        try:
            if course.url:
                os.remove(course.url)
        except OSError:
            pass
        course.delete()


def get_already_delivered(courseware, user):
    try:
        return UserCourseware.objects.get(raw=courseware, user=user)
    except UserCourseware.DoesNotExist:
        return None

#===============================================================================
# # separate list to list of lists with n size
# def grouper(col, n):
#    return izip_longest(*[iter(col)]*n)
# 
# def push_update_messages(push_dict):
#    for url, params in push_dict.iteritems():
#        for d, b, m in izip(*(grouper(x, settings.BATCH_INFORM_COUNT) for x in params)):
#            if not any(x is None for x in (d,b,m)):
#                params = {
#                    'devicetoken[]': d,
#                    'msg[]': m,
#                    'badge[]': b
#                    }
#                params = urllib.urlencode(params, True)
#                try:
#                    res = urllib.urlopen(url, params)
#                    #print >>sys.stderr, url, 'push response: ', res.read()
#                    if res.read():
#                        return False
#                except:
#                    return False
#    return True
#===============================================================================
                
#===============================================================================
# def inform(informer, classes, users, message):
#    msg = models.InformMessage.objects.create(user=informer, message=message)
#    profiles = models.UserProfile.objects.filter(Q(stu_class__in=classes) | Q(user__in=users))
#    for profile in profiles:
#        #print >>sys.stderr, profile.stu_class_id, classes
#        stucls = str(profile.stu_class_id) in classes and profile.stu_class_id or None
#        models.MessageUsers.objects.create(message=msg, user_id=profile.user_id, cls_id=stucls)
#    # push_dict = {}
#    # for profile in profiles:
#    #     push_url = settings.PUSH_URL.get(profile.app_version, '')
#    #     if push_url:
#    #         try:
#    #             devices,badges,messages = push_dict[push_url]
#    #         except KeyError:
#    #             devices = []
#    #             badges = []
#    #             messages = []
#    #             push_dict[push_url] = (devices, badges, messages)
#    #         devices.append(profile.device_id)
#    #         badges.append(0)
#    #         messages.append(message.encode('utf-8'))
#    # #print >>sys.stderr, push_dict
#    # push_update_messages(push_dict)
#    InformThread(models.MSG_STATE_INIT).start()
#===============================================================================
    
#===============================================================================
# def push_inform(state):
#    messages = models.MessageUsers.objects.select_related().filter(state=state)
#    push_dict = {}
#    msg_ids = []
#    suc_ids = []
#    fail_ids = []
#    for msg in messages:
#        profile = msg.user.userprofile
#        push_url = settings.PUSH_URL.get(profile.app_version, '')
#        if push_url:
#            try:
#                devices,badges,messages = push_dict[push_url]
#            except KeyError:
#                devices = []
#                badges = []
#                messages = []
#                push_dict[push_url] = (devices, badges, messages)
#            devices.append(profile.device_id)
#            badges.append(0)
#            messages.append(msg.message.message.encode('utf-8'))
#            msg_ids.append(msg.id)
#            if len(msg_ids) == settings.BATCH_INFORM_COUNT:
#                if push_update_messages(push_dict):
#                    suc_ids += msg_ids
#                else:
#                    fail_ids += msg_ids
#                msg_ids = []
#                push_dict = {}
#    if push_update_messages(push_dict):
#        suc_ids += msg_ids
#    else:
#        fail_ids += msg_ids
#    if suc_ids:
#        models.MessageUsers.objects.filter(id__in=suc_ids).update(state=models.MSG_STATE_PUSHED)
#    if fail_ids:
#        models.MessageUsers.objects.filter(id__in=fail_ids).update(state=models.MSG_STATE_PUSH_ERROR)
#    print >>sys.stderr, suc_ids, fail_ids
#    
# class InformThread(Thread):
#    def __init__(self, state):
#        Thread.__init__(self)
#        self.process_state = state
# 
#    def run(self):
#        push_inform(self.process_state)
#===============================================================================
