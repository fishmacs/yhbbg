from functools import wraps

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.utils.decorators import available_attrs
from django.contrib.sessions.models import Session

def user_login_test(test_func):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return HttpResponse(status=333)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    return decorator

def login_required(function=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_login_test(
        lambda u: u.is_authenticated(),
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def check_token(function=None):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            token = args[0]
            uid = int(args[1])
            try:
                session = Session.objects.get(pk=token)
                sd = session.get_decoded()
                uid1 = sd.get('_auth_user_id')
                if uid != uid1:
                    return HttpResponse(status=501)
                request.session = sd
                if request.user.is_authenticated() and request.user.id != uid:
                    request.user = User.objects.get(pk=uid)
                return view_func(request, *args, **kwargs)
            except Session.DoesNotExist:
                return HttpResponse(status=501)
        return wraps(view_func, assigned=available_attrs(view_func))(_wrapped_view)
    if function:
        return decorator(function)
    return decorator
