import json

from django.db import models
from django.contrib.auth.models import User

from common.models import Courseware


class Test(models.Model):
    TYPES = {
        'ss': 'single choice',
        'sm': 'multiple choice',
        'fk': 'keyboard input',
        'fm': 'manual input',
        'p': 'yesno'
    }
    
    courseware = models.ForeignKey(Courseware)
    section = models.CharField(max_length=20)
    title = models.CharField(max_length=20)
    seq = models.SmallIntegerField()
    type = models.CharField(max_length=2)
    num = models.SmallIntegerField()
    answer = models.CharField(max_length=256)
    page = models.SmallIntegerField()
    grid = models.SmallIntegerField()
    hint = models.TextField()

    @property
    def is_selection(self):
        return self.type.startswith('s')

    @property
    def is_fill(self):
        return self.type.startswith('f')

    @property
    def is_yesno(self):
        return self.type == 'p'

    @property
    def has_answer(self):
        return self.is_selection or self.is_yesno or self.type == 'fk'

    def get_type(self):
        return self.TYPES[self.type]

    def get_answer(self):
        return json.loads(self.answer)
        

class TestResult(models.Model):
    test = models.ForeignKey(Test)
    user = models.ForeignKey(User)
    answer = models.CharField(max_length=256)
    score = models.SmallIntegerField()