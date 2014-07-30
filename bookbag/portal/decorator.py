from functools import wraps

from django.http import HttpResponse
from django.utils.decorators import available_attrs


def authenticated_required(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _view_wrapper(request, *args, **kwargs):
        if request.user.is_authenticated():
            return view_func(request, *args, **kwargs)
        return HttpResponse(status=401)
    return _view_wrapper
    
            