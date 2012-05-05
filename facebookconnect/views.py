import datetime
import hashlib
import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from facebookconnect.models import FacebookUser

def login_facebook_connect(request):
    print request.POST
    status = 'unknown failure'
    try:
        userid = request.POST['userid']
        username = request.POST['username']
        email = request.POST['email']

        try:
            fb = FacebookUser.objects.get(facebook_id=userid)
            status = "logged in existing user"
            print fb
        except FacebookUser.DoesNotExist:
            try:
                profile = Profile.objects.get(primary_email=email)
            except Profile.DoesNotExist:
               pass 
                
            contrib_user = User()
            contrib_user.save()
            contrib_user.username = u"fbuser_%s" % contrib_user.id
            print contrib_user.username

            fb = FacebookUser()
            fb.facebook_id = user
            fb.contrib_user = contrib_user

            temp = hashlib.new('sha1')
            temp.update(str(datetime.datetime.now()))
            password = temp.hexdigest()

            contrib_user.set_password(password)
            fb.contrib_password = password
            fb.save()
            contrib_user.save()
            status = "created new user"
            print fb
            authenticated_user = auth.authenticate(
                                         username=fb.contrib_user.username, 
                                         password=fb.contrib_password)
            auth.login(request, authenticated_user)
        else:
            status = 'wrong hash sig'

            logging.debug("FBConnect: user %s with exit status %s" % (user, status))

    except Exception, e:
        logging.debug("Exception thrown in the FBConnect ajax call: %s" % e)
        print repr(e)

    return HttpResponse("%s" % status)

def start(request):
    return render_to_response('facebookconnect/start.html')

def xd_receiver(request):
    print 'here'
    return render_to_response('facebookconnect/xd_receiver.html')
