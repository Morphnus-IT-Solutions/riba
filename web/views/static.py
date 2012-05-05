# Create your views here.
import logging
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponsePermanentRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from feedback.models import Feedback
from web.forms import ContactUsForm
from notifications.email import Email
from django.template import Context, Template
from django.template.loader import get_template
from datetime import datetime

log = logging.getLogger('request')

def page(request, page):
    try:
        return render_to_response('pages/%s.html' % page, None,
                context_instance = RequestContext(request))
    except:
        raise Http404

def section_page(request, section, page):
    try:
        return render_to_response('pages/%s/%s.html' % (section, page), None,
                context_instance = RequestContext(request))
    except:
        raise Http404

def double_section_page(request, section1, section2, page):
    try:
        return render_to_response('pages/%s/%s/%s.html' % (section1, section2, page), None,
                context_instance = RequestContext(request))
    except:
        raise Http404

def contact_us(request):
    if request.method == "POST":
        form = ContactUsForm(request.POST)
        if form.is_valid():
            contact_us = form.save(commit=False)
            contact_us.submitted_on = datetime.now()
            contact_us.client = request.client.client
            contact_us.save()
            t_body = get_template('notifications/feedback/contactus.email')
            email_body = {}
            email_body['contact_us'] = contact_us
            c_body = Context(email_body)
            mail_obj = Email()
            mail_obj.isHtml = True
            mail_obj._from = request.client.client.noreply_email
            mail_obj.body = t_body.render(c_body)
            mail_obj.subject = "Contact-Us Form"
            u_emails = contact_us.email
            u_emails = u_emails.strip(',')
            mail_obj.to = "support@futurebazaar.com"
            mail_obj.send()
            return render_to_response('pages/about/thank_you-contactus.html',None,context_instance = RequestContext(request))
    else:
        form = ContactUsForm()
    return render_to_response('pages/about/contactus.html', 
        {
            'form':form,
        },context_instance = RequestContext(request))
