#encoding=utf-8

from django import forms
from django.forms.extras.widgets import SelectDateWidget

from bookbag.common import models, global_def as common_def
import db_util
import cache


class CoursewareForm(forms.Form):
    title = forms.CharField(label=u'课件名称', max_length=80, min_length=1)
    #grade = forms.ChoiceField(label=u'课件年级', choices=())
    provider = forms.ChoiceField(label=u'课件版本', choices=())
    category = forms.ChoiceField(label=u'课件类型', choices=())
    share = forms.ChoiceField(label=u'共享级别', choices=common_def.SHARE_LEVELS)
    description = forms.CharField(
        label=u'课件描述',
        widget=forms.Textarea(attrs={'cols': 20, 'rows': 6}),
        required=False)
    week = forms.IntegerField(label=u'第 几 周 ', min_value=1, max_value=30)
    file = forms.FileField(label=u'课件文件')
    image = forms.ImageField(label=u'课件图片', required=False)
    password = forms.CharField(label=u'输入密码', widget=forms.PasswordInput,
                               required=False)
    password1 = forms.CharField(label=u'重复密码', widget=forms.PasswordInput,
                                required=False)
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

    def clean_password1(self):
        p = self.cleaned_data['password']
        p1 = self.cleaned_data['password1']
        if p != p1:
            raise forms.ValidationError(u'密码不匹配')
        return p


class NameForm(forms.Form):
    name = forms.CharField(label='', max_length=20,
                           min_length=1, required=False)


class ClassNameForm(forms.Form):
    classname = forms.CharField(label='', max_length=20,
                                min_length=1, required=False)


class UsernameForm(forms.Form):
    username = forms.CharField(label='', max_length=20,
                               min_length=1, required=False)
    kind = forms.ChoiceField(label='', choices=(
        ('username', u'id'),
        ('fullname', u'姓名'),
    ))


class GradeForm(forms.Form):
    grade = forms.ChoiceField(label=u'选择年级', choices=(),
                              widget=forms.Select(attrs={
                                  'onchange': 'this.form.submit();'}))


class SearchCourseForm(forms.Form):
    course = forms.CharField(label='', max_length=30,
                             min_length=1, required=False)
    type = forms.ChoiceField(label='', choices=(
        ('name', u'课程名'),
        ('ename', u'英文名'),
        ('id', u'课程代码'),
        ))


class SearchSchoolForm(forms.Form):
    name = forms.CharField(label='', max_length=30,
                           min_length=1, required=False)
    kind = forms.ChoiceField(label='', choices=(('name', u'学校名称'),
                                                ('code', u'学校代码')))


class SearchRegionForm(forms.Form):
    name = forms.CharField(label='', max_length=16,
                           min_length=1, required=False)
    kind = forms.ChoiceField(label='', choices=(
        ('name', u'区域名称'),
        ('code', u'区域代码'),
        ))


class ImageUploadForm(forms.Form):
    image = forms.ImageField(label=u'课程图片')


#=============================================================================
# class CourseForm(forms.Form):
#    description = forms.CharField(
#        label=u'课程介绍',
#        widget=forms.Textarea(attrs={'cols': 20, 'rows': 6}),
#        required=False)
#    image = forms.ImageField(label=u'课程图片', required=False)
#=============================================================================

class OfflineTimeoutForm(forms.Form):
    offline_timeout = forms.CharField(label=u'离线时限')

    def clean_offline_timeout(self):
        s = self.cleaned_data['offline_timeout'].strip()
        try:
            int(s)
            return s
        except ValueError:
            raise forms.ValidationError(u'请输入数字')


def get_admin_types(user):
    lst = []
    if user.has_perm('auth.change_sysadmin'):
        lst.append((common_def.USERTYPE_SYSTEM_ADMIN, u'系统管理员'))
    if user.has_perm('auth.change_regionadmin'):
        lst.append((common_def.USERTYPE_REGION_ADMIN, u'区域管理员'))
    if user.has_perm('auth.change_schooladmin'):
        lst.append((common_def.USERTYPE_SCHOOL_ADMIN, u'学校管理员'))
    if len(lst) > 1:
        lst = sorted(lst, key=lambda x: -x[0])
        lst.insert(0, (0, u'请选择管理员类型'))
    return lst


class AdminForm(forms.Form):
    type = forms.ChoiceField(label=u'身份', choices=(),
                             widget=forms.Select(attrs={
                                 'onchange': 'this.form.submit();'}))
    username = forms.CharField(label=u'用户ID', max_length=30, min_length=1)
    password = forms.CharField(label=u'输入密码', widget=forms.PasswordInput)
    password1 = forms.CharField(label=u'重复密码', widget=forms.PasswordInput)
    name = forms.CharField(label=u'姓名', max_length=30,
                           min_length=1, required=False)
    email = forms.EmailField(label=u'电子邮件')

    def clean_type(self):
        t = int(self.cleaned_data['type'])
        if t > 0:
            return t
        else:
            raise forms.ValidationError(u'请选择管理员类型')


class RegionAdminForm(AdminForm):
    region = forms.ChoiceField(label=u'地区', choices=((0, u'请选择地区')))

    def clean_region(self):
        r = int(self.cleaned_data['region'])
        if r > 0:
            return r
        else:
            raise forms.ValidationError(u'请选择地区')


class SchoolAdminForm(AdminForm):
    school = forms.ChoiceField(label=u'学校', choices=((0, u'请选择学校')))

    def clean_school(self):
        s = int(self.cleaned_data['school'])
        if s > 0:
            return s
        else:
            raise forms.ValidationError(u'请选择学校')


# add
def adminForm(user, region=None, data=None):
    types = get_admin_types(user)
    if data:
        t = int(data['type'])
        if t == common_def.USERTYPE_REGION_ADMIN:
            form = RegionAdminForm(data)
            form.fields['region'].choices = cache.get_all_regions()
        elif t == common_def.USERTYPE_SCHOOL_ADMIN:
            form = SchoolAdminForm(data)
            form.fields['school'].choices = cache.get_region_schools(region)
        else:
            form = AdminForm(data)
    else:
        if len(types) > 1:
            form = AdminForm()
        else:
            t = types[0][0]
            if t == common_def.USERTYPE_REGION_ADMIN:
                form = RegionAdminForm()
                form.fields['region'].choices = cache.get_all_regions()
            elif t == common_def.USERTYPE_SCHOOL_ADMIN:
                form = SchoolAdminForm()
                form.fields['school'].choices = cache.get_region_schools(region)
    form.fields['type'].choices = types
    return form


# edit
def adminForm1(user, profile, data, region=None, is_post=False):
    t = int(data['type'])
    if t == common_def.USERTYPE_REGION_ADMIN:
        form = is_post and RegionAdminForm(data) or RegionAdminForm(initial=data)
        form.fields['region'].choices = cache.get_all_regions()
    elif t == common_def.USERTYPE_SCHOOL_ADMIN:
        form = is_post and SchoolAdminForm(data) or SchoolAdminForm(initial=data)
        form.fields['school'].choices = cache.get_region_schools(region)
    else:
        form = is_post and AdminForm(data) or AdminForm(initial=data)
    form.fields['password'].required = False
    form.fields['password1'].required = False
    #form.fields['type'].widget.attrs['style'] = 'readonly: true;'
    form.fields['type'].choices = get_admin_types(user)
    return form


GENDER = (
    ('M', u'男'),
    ('F', u'女'),
)


def get_user_types():
    lst = [x for x in common_def.USER_TYPES.items() if x[0] <= common_def.USERTYPE_TEACHER]
    lst = sorted(lst, key=lambda x: x[0])
    return tuple(lst)


class UserForm(forms.Form):
    grade = forms.ChoiceField(label=u'年级', choices=((0, u'请选择年级')),
                              widget=forms.Select(attrs={
                                  'onchange': 'this.form.submit();'}))
    myclass = forms.ChoiceField(label=u'班级', choices=((0, u'请选择班级')))
    username = forms.CharField(label=u'用户ID', max_length=30, min_length=1)
    password = forms.CharField(label=u'输入密码', widget=forms.PasswordInput)
    password1 = forms.CharField(label=u'重复密码', widget=forms.PasswordInput)
    name = forms.CharField(label=u'姓名', max_length=30, min_length=1)
    gender = forms.ChoiceField(label=u'性别', choices=GENDER)
    birthday = forms.DateField(label=u'生日')
    email = forms.EmailField(label=u'电子邮件(可选)', required=False)
    tel = forms.CharField(label=u'电话(可选)', required=False)

    def clean_password1(self):
        p = self.cleaned_data['password']
        p1 = self.cleaned_data['password1']
        if p != p1:
            raise forms.ValidationError(u'密码不匹配')
        return p

    def clean_grade(self):
        grade = self.cleaned_data['grade']
        if grade == '0':
            raise forms.ValidationError(u'请选择年级')
        return int(grade)

    def clean_myclass(self):
        clas = self.cleaned_data['myclass']
        if clas == '0':
            raise forms.ValidationError(u'请选择班级')
        return int(clas)


class TeacherForm(forms.Form):
    username = forms.CharField(label=u'用户ID', max_length=30, min_length=1)
    password = forms.CharField(label=u'输入密码', widget=forms.PasswordInput)
    password1 = forms.CharField(label=u'重复密码', widget=forms.PasswordInput)
    name = forms.CharField(label=u'姓名', max_length=30,
                           min_length=1, required=False)
    gender = forms.ChoiceField(label=u'性别', choices=GENDER)
    email = forms.EmailField(label=u'电子邮件')
    telphone = forms.CharField(label=u'电话', max_length=16)
    #type = forms.ChoiceField(label=u'身份', choices=get_user_types())

    def clean_password1(self):
        p = self.cleaned_data['password']
        p1 = self.cleaned_data['password1']
        if p != p1:
            raise forms.ValidationError(u'密码不匹配')
        return p


class SchoolForm(forms.ModelForm):
    class Meta:
        model = models.School
        fields = ('name', 'code', 'type', 'description',
                  'address', 'telphone', 'email')

    def clean_type(self):
        t = self.cleaned_data['type']
        if not t or t == '0':
            raise forms.ValidationError(u'请选择学校类型')
        return int(t)


class CourseForm(forms.ModelForm):
    class Meta:
        model = models.Course
        fields = ('course_name', 'cid', 'english_name', 'description', 'image')

#=============================================================================
# class CourseForm1(forms.ModelForm):
#    class Meta:
#        model = models.Course
#        fields = ('description', 'professor', 'image')#, 'start_date', 'end_date')
#=============================================================================


class ClassForm(forms.ModelForm):
    class Meta:
        model = models.SchoolClass
        fields = ('name',)


class ClassCourseForm(forms.Form):
    grade = forms.ChoiceField(label=u'年级', choices=(),
                              widget=forms.Select(attrs={
                                  'onchange': 'this.form.submit();'}))
    myclass = forms.MultipleChoiceField(label=u'班级', choices=(),
                                        widget=forms.SelectMultiple(attrs={
                                            'style': 'width:100px;'}))
    course = forms.MultipleChoiceField(label=u'课程', choices=(),
                                       widget=forms.SelectMultiple(attrs={
                                           'style': 'width:100px;'}))

    def clean_grade(self):
        grade = self.cleaned_data['grade']
        if grade == '0':
            raise forms.ValidationError(u'请选择年级')
        return int(grade)

    def clean_myclass(self):
        classes = self.cleaned_data['myclass']
        if not classes:
            raise forms.ValidationError(u'请选择班级')
        return [int(c) for c in classes]

    def clean_course(self):
        courses = self.cleaned_data['course']
        if not courses:
            raise forms.ValidationError(u'请选择课程')
        return [int(course) for course in courses]

    def set_choices(self, session, grade):
        self.fields['grade'].choices = common_def.get_all_grades(
            session['school_type'], prompt=True)
        self.fields['myclass'].choices = cache.get_grade_classes(
            session['school'], grade, prompt=False)
        self.fields['course'].choices = cache.get_grade_courses(
            session['region'], session['school'], grade)


class SemesterForm(forms.ModelForm):
    class Meta:
        model = models.Semester
        fields = ('name', 'start_date', 'end_date')


class MessageForm(forms.Form):
    message = forms.CharField(
        label=u'通知消息',
        widget=forms.Textarea(attrs={'cols': 20, 'rows': 6}))


class UserImportForm(forms.Form):
    file = forms.FileField(label=u'用户文件')


class RegionForm(forms.ModelForm):
    class Meta:
        model = models.Region
        fields = ('name', 'code')


class DateTimeForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(DateTimeForm, self).__init__(*args, **kwargs)
        for _, field in self.fields.iteritems():
            field.widget.attrs.update({'class': 'smallfont'})
        self.fields['manual'].widget.attrs.update({
            'class': 'smallfont inline'})

    date = forms.DateField(widget=SelectDateWidget)
    hour = forms.ChoiceField(choices=((x, x) for x in xrange(0, 24)))
    minute = forms.ChoiceField(choices=((x, x) for x in xrange(0, 60, 5)))
    manual = forms.BooleanField(label=u'手动开始', required=False)
