from django.db.transaction import commit_on_success
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from bookbag.common import global_def as common_def
import db_util

@commit_on_success
def perms():
    
    ct_user = ContentType.objects.get(name='user', app_label='auth')
    perm_sysadm,_ = Permission.objects.get_or_create(name='Can operate sysadmin', content_type=ct_user, codename='change_sysadmin')
    perm_regionadm,_ = Permission.objects.get_or_create(name='Can operate regionadmin', content_type=ct_user, codename='change_regionadmin')
    perm_schooladm,_ = Permission.objects.get_or_create(name='Can operate schooladmin', content_type=ct_user, codename='change_schooladmin')
    perm_teacher,_ = Permission.objects.get_or_create(name='Can operate teacher', content_type=ct_user, codename='change_teacher')    
    perm_student,_ = Permission.objects.get_or_create(name='Can operate student', content_type=ct_user, codename='change_student')

    ct_region = ContentType.objects.get(model='region', app_label='common')
    perm_region,_ = Permission.objects.get_or_create(name='Can change region', content_type=ct_region, codename='change_region')

    ct_school = ContentType.objects.get(model='school', app_label='common')
    perm_school,_ = Permission.objects.get_or_create(name='Can change school', content_type=ct_school, codename='change_school')

    ct_class = ContentType.objects.get(model='schoolclass', app_label='common')
    perm_class,_ = Permission.objects.get_or_create(name='Can change school class', content_type=ct_class, codename='change_schoolclass')
    
    ct_course = ContentType.objects.get(model='course', app_label='common')
    perm_course,_ = Permission.objects.get_or_create(name='Can change course', content_type=ct_course, codename='change_course')

    ct_courseware = ContentType.objects.get(model='courseware', app_label='common')
    perm_courseware,_ = Permission.objects.get_or_create(name='Can change courseware', content_type=ct_courseware, codename='change_courseware')

    ct_semester = ContentType.objects.get(model='semester', app_label='common')
    perm_semester,_ = Permission.objects.get_or_create(name='Can change semester', content_type=ct_semester, codename='change_semester')

    ct_bookprov = ContentType.objects.get(model='bookprovider', app_label='common')
    perm_bookprov,_ = Permission.objects.get_or_create(name='Can change book provider', content_type=ct_bookprov, codename='change_bookprovider')

    ct_cwcategory = ContentType.objects.get(model='coursewarecategory', app_label='common')
    perm_cwcategory,_ = Permission.objects.get_or_create(name='Can change courseware category', content_type=ct_cwcategory, codename='change_coursewarecategory')

    ct_schedule = ContentType.objects.get(model='courseschedule', app_label='common')
    perm_schedule,_ = Permission.objects.get_or_create(name='Can change course schedule', content_type=ct_schedule, codename='change_courseschedule')

    ct_scontact = ContentType.objects.get(model='schoolcontacts', app_label='common')
    perm_scontact,_ = Permission.objects.get_or_create(name='Can change school contacts', content_type=ct_scontact, codename='change_schoolcontacts')

    ct_ccontact = ContentType.objects.get(model='classcontacts', app_label='common')
    perm_ccontact,_ = Permission.objects.get_or_create(name='Can change class contacts', content_type=ct_ccontact, codename='change_classcontacts')

    gp_sysadm,_ = Group.objects.get_or_create(name='sysadmin')
    gp_regionadm,_ = Group.objects.get_or_create(name='regionadmin')
    gp_schooladm,_ = Group.objects.get_or_create(name='schooladmin')
    gp_teacher,_ = Group.objects.get_or_create(name='teacher')

    gp_sysadm.permissions.add(perm_sysadm, perm_regionadm, perm_region, perm_course, perm_bookprov, perm_cwcategory)
    gp_regionadm.permissions.add(perm_schooladm, perm_school, perm_bookprov, perm_cwcategory, perm_semester)
    gp_schooladm.permissions.add(perm_teacher, perm_student, perm_class, perm_semester, perm_bookprov, perm_cwcategory, perm_schedule, perm_scontact, perm_ccontact)
    gp_teacher.permissions.add(perm_courseware)
    
    # users = User.objects.select_related('userprofile').filter(userprofile__usertype__gte=global_vas.USERTYPE_TEACHER)
    # for u in users:
    #     if u.userprofile.usertype == global_vars.USERTYPE_SYSTEM_ADMIN:
    #         u.groups.add(gp_sysadm)
    #     elif u.userprofile.usertype == global_vars.USERTYPE_REGION_ADMIN:
    #         u.groups.add(gp_regionadm)
    #     elif u.userprofile.usertype == global_vars.USERTYPE_SCHOOL_ADMIN:
    #         u.groups.add(gp_schooladm)
    #     else:
    #         u.groups.add(gp_teacher)
    print 'ok'

@commit_on_success
def admin():
    admin = User.objects.create(username='admin', is_staff=True, email='test@palmtao.com')
    admin.set_password('admin123')
    admin.save()
    admin.groups.add(db_util.group_of_usertype(common_def.USERTYPE_SYSTEM_ADMIN))
    profile = admin.userprofile
    profile.usertype = common_def.USERTYPE_SYSTEM_ADMIN
    profile.save()
