from django.db import models

from common.modles import Courseware


class Test(models.Model):
    courseware = models.ForeignKey(Courseware)
    section = models.CharField(max_length=20)
    seq = models.SmallIntegerField()
    type = models.CharField(max_length=2)
    num = models.SmallIntegerField()
    answer = models.CharField(max_length=256)
    
    def is_selection(self):
        return self.type.startswith('s')

    def is_fill(self):
        return self.type.startswith('f')
        
    def has_answer(self):
        return self.is_selection() or self.type == 'fk'

    

    