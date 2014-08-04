import uuid

from django.conf import settings

from portal.decorator import authenticated_required
from common.decorator import json_wrapper
from portal import db_util
from common import util
import models
import msgq


@authenticated_required
@json_wrapper
def controllers(request):
    courses = db_util.get_course_list1(request.user, request.session)
    class_ids, course_ids = zip(*[(clsid, course.id) for clsid, course in courses])
    qs = models.LessonSync.objects.filter(course__in=course_ids, myclass__in=class_ids)
    sync = {}
    if len(qs):
        s = qs[0]
        if not s.finished:
            sync = {'sync_id': s.uuid,
                    #'course_id': s.course_id,
                    'destination': '/dsub/sync__{0}'.format(s.uuid),
                    'message_queue': settings.MESSAGE_QUEUE}
    ctrls = [{
        #'course_id': x.course_id,
        'destination': '/topic/course__{0}_{1}'.format(x.myclass_id, x.course_id),
        'message_queue': settings.MESSAGE_QUEUE}
        for x in qs
    ]
    return {'controllers': ctrls, 'sync': sync}
    

@authenticated_required
@json_wrapper
def sync_get(request):
    courses = db_util.get_course_list1(request.user, request.session)
    class_ids, course_ids = zip(*[(clsid, course.id) for clsid, course in courses])
    qs = models.LessonSync.objects.filter(course__in=course_ids, myclass__in=class_ids)
    data = {}
    if len(qs):
        s = qs[0]
        if not s.finished:
            data = {'sync_id': s.uuid,
                    #'course_id': s.course_id,
                    'destination': '/dsub/sync__{0}'.format(s.uuid),
                    'message_queue': settings.MESSAGE_QUEUE}
    return data
    

@authenticated_required
@json_wrapper
def sync_start(request, class_id, course_id):
    id = uuid.uuid1().get_hex()
    models.LessonSync.objects.create(
        uuid=id,
        course_id=course_id,
        myclass_id=class_id,
        creator=request.user
    )
    destination = '/topic/course__{0}_{1}'.format(class_id, course_id)
    data = {'command': 'start_sync',
            'sync_id': id,
            'controller': destination,
            'destination': '/dsub/sync__{0}'.format(id),
            'message_queue': settings.MESSAGE_QUEUE}
    msgq.send(msgq.DAEMON_CHANNEL, data)
    #msgq.subscribe_sync(id)
    return data

    
@authenticated_required
@json_wrapper
def sync_end(request, id):
    sync = models.LessonSync.objects.get(uuid=id)
    sync.finished = True
    sync.save()
    #msgq.unsubscribe_sync(id)
    destination = '/topic/course__{0}_{1}'.format(sync.myclass_id, sync.course_id)
    data = {'command': 'end_sync',
            'sync_id': id,
            'controller': destination,
            'destination': '/dsub/sync__{0}'.format(id),
            'message_queue': settings.MESSAGE_QUEUE}
    msgq.send(msgq.DAEMON_CHANNEL, data)
