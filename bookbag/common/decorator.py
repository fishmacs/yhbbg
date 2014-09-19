#encoding=utf-8

from functools import wraps

from django.http import HttpRequest, HttpResponse
from django.core.cache import cache
from django.utils.decorators import available_attrs

import util


class BookbagError(ValueError):
    pass

    
def json_wrapper(_func):
    @wraps(_func, assigned=available_attrs(_func))
    def _wrapper(*args, **kwargs):
        try:
            data = {
                'result': 'ok',
                'reason': '',
                'data': _func(*args, **kwargs)
            }
            return HttpResponse(util.jsondumps(data))
        except BookbagError as e:
            return HttpResponse(util.fail(str(e)))
        # except Exception as e:
        #     import traceback
        #     traceback.print_exc()
        #     return HttpResponse(util.error(e.message))
    return _wrapper

             
def cache_properties(name, duration):
    def _decorator(_func):
        @wraps(_func, assigned=available_attrs(_func))
        def _wrapper(*args, **kwargs):
            key = get_cache_key(name, *args, **kwargs)
            data = cache.get(key)
            if not data:
                data = _func(*args, **kwargs)
                cache.set(key, data, duration)
            return data
        return _wrapper
    return _decorator


def clear_prop_cache(name):
    def _decorator(_func):
        @wraps(_func, assigned=available_attrs(_func))
        def _wrapper(*args, **kwargs):
            ret = _func(*args, **kwargs)
            key = get_cache_key(name, *args, **kwargs)
            cache.delete(key)
            return ret
        return _wrapper
    return _decorator
    

def get_cache_key(name, *args, **kwargs):
    if args and isinstance(args[0], HttpRequest):
        key_args = args[1:]
    else:
        key_args = args
    newargs = [unicode(arg) for arg in key_args] + ['{0}:{1}'.format(k, v) for k, v in kwargs]
    return '{0}__{1}:properties'.format(name, '_'.join(newargs))
