import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.fbsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
	sys.path.insert(1, PARENT_FOLDER)

from django import db
from web.views import webmaster
from accounts.models import *
import traceback
import sys
from django.core.mail import EmailMessage
import socket, struct, fcntl

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sockfd = sock.fileno()
SIOCGIFADDR = 0x8915

def get_ip(iface = 'eth0'):
    ifreq = struct.pack('16sH14s', iface, socket.AF_INET, '\x00'*14)
    try:
        res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
        return None
    ip = struct.unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)

def send_email_notification(notify_for, stack_trace):
    body = stack_trace
    ip_address = get_ip('eth0')
    subject = 'Catalog Feeds failed for %s from IP - %s' % (notify_for, ip_address)
    msg = EmailMessage(subject, body,
        "Future Bazaar Reports<lead@futurebazaar.com>",
        ['kishan.gajjar@futuregroup.in', 'Krishna.Raghavan@futuregroup.in', 'Hemanth.Goteti@futuregroup.in'])
    msg.send()

if __name__ == '__main__':
    class X:
        pass
    request = X()
    request.client = ClientDomain.objects.get(domain='www.futurebazaar.com')
    try:
        webmaster.gen_sitemap(request)
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("GENERIC SITEMAP", st)
    try:
        webmaster.gen_category_feeds(request)
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("GENERIC CATEGORY", st)
    try:
        webmaster.gen_web_feeds(request, 'dgm')
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("GENERIC DGM FEEDS", st)
    try:
        webmaster.gen_omg_feeds(request)
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("GENERIC OMG FEEDS", st)
    try:
        webmaster.gen_web_feeds(request, '9dot')
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("GENERIC 9DOT FEEDS", st)
    try:
        webmaster.gen_web_feeds(request, 'vc')
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("GENERIC VC FEEDS", st)
    try:
        webmaster.gen_daily_deal_feed(request, 'general')
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("DAILY DEAL FEEDS", st)
    try:
        webmaster.gen_daily_deal_feed(request, 'dgm')
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("DAILY DEAL DGM FEEDS", st)
    try:
        webmaster.gen_daily_deal_feed(request, 'omg')
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("DAILY DEAL OMG FEEDS", st)
    try:
        webmaster.gen_daily_deal_feed(request, '9dot')
    except Exception,e:
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        send_email_notification("DAILY DEAL 9DOT FEEDS", st)
