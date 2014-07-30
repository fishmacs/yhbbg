import sys
import os
from datetime import datetime

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned

from common import models, global_def as common_def
import converter


def deliver_user_courseware(user, courseware):
    profile = user.get_profile()
    device_id = profile and profile.device_id or ''
    if device_id:
        try:
            path = converter.deliver_file(
                courseware.id, user.id,
                courseware.outpath, device_id)
            finished = models.UserCourseware.objects.create(
                user=user, raw=courseware, url=path)
            return finished
        except Exception, e:
            print >>sys.stderr, 'deliver failed: ', e
    return None


def redeliver(user, courseware):
    profile = user.get_profile()
    device_id = profile and profile.device_id or ''
    if device_id:
        try:
            path = converter.deliver_file(courseware.id, user.id,
                                          courseware.outpath, device_id)
            # make output file(path) can been seen
            os.listdir(os.path.dirname(path))
            return path
        except Exception, e:
            print >>sys.stderr, 'deliver failed: ', e
    return ''


def courseware_user_state(courseware, user):
    downloaded = False
    try:
        uc = get_newest_courseware(courseware, user)
        #UserCourseware.objects.get(raw=courseware, user=user)
        if uc.download_time:
            downloaded = True
            if uc.download_time > courseware.modified_time:
                return False, downloaded
    except models.UserCourseware.DoesNotExist:
        pass
    td = datetime.now() - courseware.modified_time
    return td.seconds + td.days * 86400 < settings.COURSEWARE_NEW_DURATION, downloaded


def get_newest_courseware(courseware, user):
    try:
        return models.UserCourseware.objects.get(raw=courseware, user=user)
    except MultipleObjectsReturned:
        l = models.UserCourseware.objects.filter(raw=courseware, user=user).order_by('-created_time')
        print >>sys.stderr, 'Multiple user courseware found! user: %d, courseware: %d' % (user.id, courseware.id)
        return l[0]


def set_courseware_undownloaded(user):
    models.UserCourseware.objects.filter(user=user).update(download_time=None)


def delete_delivered(user):
    for course in models.UserCourseware.objects.filter(user__exact=user):
        try:
            if course.url:
                os.remove(course.url)  # .encode('utf8'))
        except OSError:
            pass
        finally:
            course.delete()


def convert_finish(courseware_id, errmsg):
    courseware = models.Courseware.objects.get(pk=courseware_id)
    courseware.state = not errmsg and common_def.COURSEWARE_STATE_CONVERTED or common_def.COURSEWARE_STATE_CONVERT_ERROR
    courseware.errmsg = errmsg[:80]
    courseware.save()
