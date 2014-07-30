from django.db import models
from django.contrib.auth.models import User

from common.models import Course, SchoolClass


class LessonSync(models.Model):
    uuid = models.CharField(max_length=32, primary_key=True)
    myclass = models.ForeignKey(SchoolClass)
    course = models.ForeignKey(Course)
    creator = models.ForeignKey(User)
    created_time = models.DateTimeField(auto_now_add=True)
    finished = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_time']
        #unique_together = ('myclass', 'course')

        
class SyncAction(models.Model):
    sync = models.ForeignKey(LessonSync)
    kind = models.CharField(max_length=32)
    action = models.CharField(max_length=32)
    target = models.TextField()
    option = models.TextField()
    time = models.DateTimeField(auto_now_add=True)
