#encoding=utf-8

from mongoengine import *

#from django.utils import timezone
from datetime import datetime


class EmbeddedOwner(EmbeddedDocument):
    id = StringField(max_length=64, required=True)
    kind = StringField(max_length=32, default='course')
    name = StringField(max_length=80, required=True)
    en_name = StringField(max_length=80, default='')


class EmbeddedUser(EmbeddedDocument):
    id = StringField(max_length=80, required=True)
    name = StringField(max_length=30, required=True)


class Option(EmbeddedDocument):
    #id = IntField(required=True)
    content = StringField(max_length=200, required=True)
    count = IntField(default=0)


class Answer(EmbeddedDocument):
    voter = EmbeddedDocumentField(EmbeddedUser, required=True)
    choices = ListField(IntField(required=True), required=True)
    comment = StringField(max_length=200)


vote_types = {'single': u'单选', 'multiple': u'多选', 'multiple_ordered': u'多选有序'}


class Vote(Document):
    title = StringField(max_length=200, required=True)
    kind = StringField(choices=(('single', u'单选'), ('multiple', u'多选'),
                                ('multiple_ordered', u'多选有序')),
                       default='single')
    max_choice = IntField(default=1)
    min_choice = IntField(default=1)
    owner = EmbeddedDocumentField(EmbeddedOwner)
    creator = EmbeddedDocumentField(EmbeddedUser, required=True)
    created_time = DateTimeField(default=datetime.now)
    modifier = EmbeddedDocumentField(EmbeddedUser)
    modified_time = DateTimeField()
    start_time = DateTimeField()
    end_time = DateTimeField()
    started = BooleanField(default=False)
    finished = BooleanField(default=False)
    options = ListField(EmbeddedDocumentField(Option), required=True)
    voter_count = IntField(default=0)
    result = ListField(EmbeddedDocumentField(Answer))
    deleted = BooleanField(default=False)

    def is_active(self):
        return self.started and not self.finished
        #and (not self.end_time or self.end_time>timezone.now())

    def get_status(self):
        if not self.started:
            return u'未开始'
        elif not self.finished:
            return u'投票中...'
        return u'已结束'

    def get_kind(self):
        return vote_types.get(self.kind, u'未知')


class UserLog(Document):
    user = EmbeddedDocumentField(EmbeddedUser, required=True)
    device = StringField(max_length=32)
    action = StringField(max_length=32, required=True)
    resource_id = StringField(max_length=256)
    parameter = StringField(max_length=32)
    result = StringField(max_length=32)
    time = DateTimeField(required=True)

