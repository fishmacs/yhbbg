import base64
import httplib
import urllib, urllib2
from urlparse import urlparse

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.conf import settings
from django.http import HttpResponse

import ask

#@login_required
@csrf_exempt
def ask_search(request, grade, class_id=None):
    search_type = request.POST['search_type']
    params = {
        'format': 'json',
        'tags': ask.get_ask_tags(request, grade, class_id),
        # 'username': request.user.username,
        # 'api_key': _get_api_key(request),
        'limit': 0,
        }
    if search_type == 'thread':
        url = '%s/thread' % settings.ASK_API_URL
        # params['username'] = request.user.username,
        # params['api_key'] = _get_api_key(request),
    elif search_type == 'post':
        # params['username'] = request.user.username,
        # params['api_key'] = _get_api_key(request),
        url = '%s/post' % settings.ASK_API_URL
    else:
        return HttpResponse(status=501)
    postdata = request.POST.dict()
    del(postdata['search_type'])
    params.update(postdata)
    req = urllib2.Request('%s/?%s' %(url, urllib.urlencode(params)),
                        headers={'Content-type': 'application/json'})
    s = urllib2.urlopen(req)
    return HttpResponse(s.read())

@csrf_exempt
def api(request):
    if request.user.is_authenticated():
        username = request.user.username
    else:
        auth_succ, username = _authenticate(request)
        if not auth_succ:
            return HttpResponse(status=401)
    
    def format_header_name(name):
        return "-".join([ x[0].upper()+x[1:] for x in name[5:].lower().split('_') ])

    headers = dict([(format_header_name(k),v) for k,v in request.META.items() if k.startswith('HTTP_') and k!='HTTP_AUTHORIZATION'])
    try:
        headers["Content-type"] = request.META['CONTENT_TYPE']
    except:
        pass

    url = urlparse(settings.ASK_API_URL)
    path = request.get_full_path()
    path = path.replace('/api/v1/', url.path+'/')
    if 'format' not in request.GET:
        path += '?format=json'
    if username:
        path += '&username='+username

    if url.scheme=='http':
        conn = httplib.HTTPConnection(url.hostname, url.port)
    elif url.scheme=='https':
        conn = httplib.HTTPSConnection(url.hostname, url.port)
    conn.request(
        request.method,
        path.encode('utf8'), # there is an encoding error if path is unicode and utf8 non-ascii char in request.body, so coerce it to str. http://stackoverflow.com/questions/6582955/django-httplib-transmitting-request-raw-post-data-with-httplib
        request.raw_post_data,
        headers
    )
    response = conn.getresponse()
    return HttpResponse(response.read())
    
def _authenticate(request):
    try:
        (auth_type, data) = request.META['HTTP_AUTHORIZATION'].split()
        if auth_type != 'Basic':
            return False, None
        user_pass = base64.b64decode(data)
    except KeyError:
        return True, None
    except:
        return False, None

    bits = user_pass.split(':', 1)
    if len(bits) != 2:
        return False, None

    user = authenticate(username=bits[0], password=bits[1])
    return user and (True,user.username) or (False, None)
