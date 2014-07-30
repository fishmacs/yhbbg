'''
Created on 2012-11-27

@author: zw
'''

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

# def user_type_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
#     if not login_url:
#         from django.conf import settings
#         login_url = settings.LOGIN_URL

#     def decorator(view_func):
#         def _wrapped_view(request, *args, **kwargs):
#             if test_func(request.session['user_type']):
#                 return view_func(request, *args, **kwargs)
#             path = urlquote(request.get_full_path())
#             tup = login_url, redirect_field_name, path
#             return HttpResponseRedirect('%s?%s=%s' % tup)
#         return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
#     return decorator

def check_all_perms(user, permstr):
    f = lambda x: '.' in x and x or 'common.'+x
    perms = [f(p) for p in permstr.split()]
    return user.has_perms(perms)

def check_any_perm(user, permstr):
    f = lambda x: '.' in x and x or 'common.'+x
    perms = [f(p) for p in permstr.split()]
    for p in perms:
        if user.has_perm(p):
            return True
    return False

def has_any_permission(perms, login_url=None, raise_exception=False):
    def check_perms(user):
        if check_any_perm(user, perms):
            return True
        if raise_exception:
            raise PermissionDenied
        return False
    return user_passes_test(check_perms, login_url=login_url)

def has_all_permissions(perms, login_url=None, raise_exception=False):
    def check_perms(user):
        if check_all_perms(user, perms):
            return True
        if raise_exception:
            raise PermissionDenied
        return False
    return user_passes_test(check_perms, login_url=login_url)

def has_permission(perm, login_url=None, raise_exception=False):
    def check_perm(user):
        p = '.' in perm and perm or 'common.'+perm
        if user.has_perm(p):
            return True
        if raise_exception:
            raise PermissionDenied
        return False
    return user_passes_test(check_perm, login_url=login_url)
        
