#encoding=utf-8

from django import forms

from common import global_def as common_def
import db_util

class CoursewareForm(forms.Form):
    title = forms.CharField(
        label=u'课件名称',
        widget=forms.TextInput(attrs={'class': 'textbox'}),
        max_length=80, min_length=1)
    provider = forms.ChoiceField(
        label=u'课件版本',
        widget=forms.Select(attrs={'class': 'textbox'}),
        choices=())
    category = forms.ChoiceField(
        label=u'课件类型',
        widget=forms.Select(attrs={'class': 'textbox'}),
        choices=())
    share = forms.ChoiceField(
        label=u'共享级别',
        widget=forms.Select(attrs={'class': 'textbox'}),
        choices=common_def.SHARE_LEVELS)
    description = forms.CharField(
        label=u'课件描述',
        widget=forms.Textarea(attrs={'width': '440', 'height': '105', 'class': 'textarea'}),
        required=False)
    week = forms.IntegerField(
        label=u'第 几 周 ',
        widget=forms.TextInput(attrs={'class': 'textbox'}),
        min_value=1, max_value=30)
    file = forms.FileField(label=u'课件文件')
    image = forms.ImageField(label=u'课件图片', required=False)
    # password = forms.CharField(label=u'输入密码', widget=forms.PasswordInput, required=False)
    # password1 = forms.CharField(label=u'重复密码', widget=forms.PasswordInput, required=False)
    classes = forms.MultipleChoiceField(label=u'选择班级')
    
    def refresh_choices(self, classes):
        #self.fields['grade'].choices = common_def.get_all_grades(school_type)
        self.fields['classes'].choices = classes
        #self.fields['classes'].initial = [c[0] for c in classes]
        self.fields['provider'].choices = db_util.get_book_providers()
        self.fields['category'].choices = db_util.get_courseware_categories()
        
    def clean_title(self):
        title = self.cleaned_data['title']
        if title:
            title = title.strip()
        if not title:
            raise forms.ValidationError(u'请填写课件名称！')
        return title

    # def clean_password1(self):
    #     p = self.cleaned_data['password']
    #     p1 = self.cleaned_data['password1']
    #     if p != p1:
    #         raise forms.ValidationError(u'密码不匹配')
    #     return p

        
class NameForm(forms.Form):
    name = forms.CharField(label='', max_length=20, min_length=1, required=False)
    
class SearchCourseForm(forms.Form):
    course = forms.CharField(label='', max_length=30, min_length=1, required=False)
    type = forms.ChoiceField(label='', choices=(
        ('name', u'课程名'),
        ('ename', u'英文名'),
        ('id', u'课程ID'),
        ))

    # def clean_course(self):
    #     course = self.cleaned_data['course'].strip()
    #     if not course:
    #         raise forms.ValidationError(u'请填写搜索的课程！')
    #     return course

