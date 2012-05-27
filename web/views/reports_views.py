from orders.models import *
from api.fbapi import *
from users.helper import *
from utils import utils
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from catalog.models import *
from locations.models import *
from orders.forms import *
from users.models import Profile,Email,Phone
from users.models import Email as UserEmail,Phone
from users.models import DailySubscription
from feedback.models import Feedback
from ccm.models import Agent
from communications.models import Call
from django.contrib import auth
from django.contrib.auth.models import User
from payments.models import PaymentAttempt
from promotions.models import Coupon
from django.contrib.auth.decorators import login_required
from payments import hdfcpg
from django.template.loader import get_template
from django.template import Context, Template
import re
from integrations.fbapi import users, orders, fbapiutils
from payments import ccAvenue
import logging
from django.utils import simplejson
from datetime import datetime,timedelta
from django.db.models import Avg, Max, Min, Count, Sum
from lists.models import *
import operator
import gviz_api
import pyExcelerator
from django.views.decorators.cache import never_cache
from notifications.notification import Notification
from notifications.email import Email
from notifications.sms import SMS
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_control
from django.utils.encoding import smart_unicode, smart_str


log = logging.getLogger('fborder')


def check_dates(request):
    from_date = request.GET.get('from','')
    to_date = request.GET.get('to','')
    search_trend = request.GET.get('search_trend','')
    errors = ""
    if search_trend:
        to_date = datetime.now()
        to_date = datetime(day=to_date.day, month=to_date.month, year=to_date.year, hour=23, minute=59, second=59)
        if search_trend == "day":
            from_date = to_date + timedelta(hours=-23, minutes=-59, seconds=-59)
        elif search_trend == "week":
            from_date = to_date + timedelta(days=-6, hours=-23, minutes=-59, seconds=-59)
        elif search_trend == "month":
            from_date = to_date + timedelta(days=-29, hours=-23, minutes=-59, seconds=-59)
        return True,from_date,to_date
    if from_date== None or from_date == "" or to_date==None or to_date== "":
        to_date = datetime.now()
        to_date = datetime(day=to_date.day, month=to_date.month, year=to_date.year, hour=23, minute=59, second=59)
        from_date = to_date + timedelta(days=-6, hours=-23, minutes=-59, seconds=-59)
        return True,from_date,to_date

    if from_date and to_date:
        from_date = datetime.strptime(from_date,'%d %b, %Y').date()
        to_date = datetime.strptime(to_date,'%d %b, %Y').date()
        from_date = datetime(day=from_date.day, month=from_date.month, year=from_date.year, hour=0, minute=0, second=0)
        to_date = datetime(day=to_date.day, month=to_date.month, year=to_date.year, hour=23, minute=59, second=59)
        if to_date < from_date:
            errors = "Please Select a Valid Date Range"
            return False,errors
        else: return True,from_date,to_date

def check_dates_subscription(request):
    from_date = request.GET.get('from','')
    to_date = request.GET.get('to','')
    search_trend = request.GET.get('search_trend','')
    errors = ""
    if from_date== None or from_date == "" or to_date==None or to_date== "":
        from_day = datetime.now().date() + timedelta(days=-1)
        from_date = datetime(day=from_day.day, month=from_day.month, year=from_day.year, hour=0, minute=0, second=0)
        to_date = datetime(day=from_day.day, month=from_day.month, year=from_day.year, hour=23, minute=59, second=59)
        return True,from_date,to_date
    else:
        return check_dates(request)

def save_excel_process(request, excel_dict, *args):
    for k in excel_dict.keys():
        save_excel = get_excel_status(request, k)
        if save_excel:
            func = excel_dict[k]
            data_list = func(*args)['list']
            return save_excel_file(request, data_list[0], data_list[1:])
    return None

def get_excel_status(request, excel):
    if excel in request.GET:
        return True
    else:
        return False

    
def save_excel_file(request, excel_header, excel_data):
    workBookDocument = pyExcelerator.Workbook()
    docSheet1 = workBookDocument.add_sheet("sheet1")

    #Create a font object *j
    myFont = pyExcelerator.Font()

    # Change the font
    myFont.name = 'Times New Roman'

    # Make the font bold, underlined and italic
    myFont.bold = True
    myFont.underline = True

# the font should be transformed to style *
    myFontStyle = pyExcelerator.XFStyle()
    myFontStyle.font = myFont

# if you wish to apply a specific style to a specific row you can use the following command
    docSheet1.row(0).set_style(myFontStyle)
#    docSheet1.write(0,column, key,myFontStyle)
    for i in range(len(excel_header)):
        if type(excel_header[i]).__name__ in ["date", "datetime"]:
            entry = str(excel_header[i].day) + '-' + str(excel_header[i].month) + '-' + str(excel_header[i].year)
        else:
            entry = str(excel_header[i])
        docSheet1.write(0, i, entry,myFontStyle)
    row = 0
    for list in excel_data:
        row = row + 1
        for i in range(len(list)):
            if list[i] is not None:
                if type(list[i]).__name__ in ["date", "datetime"]:
                    entry = str(list[i].day) + '-' + str(list[i].month) + '-' + str(list[i].year)
                    docSheet1.write(row,i,entry)
                elif type(list[i]).__name__ in ["unicode"]:
                    entry = smart_unicode(list[i], encoding = 'utf-8', strings_only = False, errors='strict')
                    #entry = unicode(list[i]).encode("utf-8")
                    docSheet1.write(row,i,entry)
                else:
                    docSheet1.write(row,i,str(list[i]))

    filename = "fileName.xls"
    response = HttpResponse(mimetype = "application/vnd.ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    workBookDocument.save(response)
    return response


def subscription_report(request):
    save_excel = get_excel_status(request, "excel")
    date = check_dates_subscription(request)
    if date[0]:
        from_date = date[1]
        to_date = date[2]
    from_date = from_date.date()
    to_date = to_date.date()
    search_trend = request.GET.get('search_trend','')
    if request.user.is_staff == True:
        staff = True
        if save_excel == True:
            data_list = subscription_report_list(from_date, to_date)['list']
            return save_excel_file(request, data_list[0], data_list[1:])
        else:
            subscription_report_dict = subscription_report_list(from_date, to_date)
            data_dict = {
                'from_date': from_date,
                'to_date': to_date,
                'search_trend': search_trend,
                'subscription_report_dict': subscription_report_dict,
                'staff': staff,
            }
        return render_to_response("reports/subscription_report.html", data_dict, context_instance=RequestContext(request))
    else:
        staff = False
        data_dict = {
            'from_date': from_date,
            'to_date': to_date,
            'search_trend': search_trend,
            'staff': False,
        }
        return render_to_response("reports/subscription_report.html", data_dict, context_instance=RequestContext(request))

def subscription_report_list(from_date, to_date):
    dsub = DailySubscription.objects.filter(timestamp__gte = from_date, timestamp__lte = to_date + timedelta(days=1))
    sources_list = list(dsub.values_list('source', flat=True).distinct())
    registrations_list = [source for source in sources_list if (source != 'facebook' and source != None)]
    sources_title = []
    for source in sources_list:
        if source == None:
            sources_title.append('Online/Phone Subscriptions')
        elif source.startswith('/'):
            sources_title.append(source[1:])
        else:
            sources_title.append(source)
    pd_data = [['Day', 'Date', 'Total Subscriptions', 'Registrations'] + sources_title]
    dates = []
    diff = (to_date - from_date).days
    for i in range(0,diff+1):
        dates.append(from_date + timedelta(days=i))
    dates.reverse()
    for date in dates:
        day = day_name_of_date(date.weekday())
        cd = DailySubscription.objects.filter(timestamp__gte = date, timestamp__lte = date+timedelta(days=1))
        sub_count = {}
        sub_count['registrations'] = cd.filter(source__in=registrations_list).count()
        date_list = [day, date, int_to_comma_seperated(cd.count()), int_to_comma_seperated(sub_count['registrations'])]
        for source in sources_list:
            sub_count[source] = cd.filter(source=source).count()
            date_list.append(int_to_comma_seperated(sub_count[source]))
        pd_data.append(date_list)
    dict = {
        'list':pd_data,
        }
    return dict

def day_name_of_date(day):
    if day == 0:
        return "Mon"
    if day == 1:
        return "Tue"
    if day == 2:
        return "Wed"
    if day == 3:
        return "Thu"
    if day == 4:
        return "Fri"
    if day == 5:
        return "Sat"
    if day == 6:
        return "Sun"

def feedback_report(request):
    save_excel = get_excel_status(request, "excel")
    date = check_dates(request)
    if date[0]:
        from_date = date[1]
        to_date = date[2]
    from_date = from_date.date()
    to_date = to_date.date()
    search_trend = request.GET.get('search_trend','')
    if request.user.is_staff == True:
        staff = True
        if save_excel == True:
            data_list = feedback_report_list(from_date, to_date)['list']
            return save_excel_file(request, data_list[0], data_list[1:])
        else:
            feedback_report_dict = feedback_report_list(from_date, to_date)
            data_dict = {
                'from_date': from_date,
                'to_date': to_date,
                'search_trend': search_trend,
                'feedback_report_dict': feedback_report_dict,
                'staff': staff
            }
        return render_to_response("reports/feedback_report.html", data_dict, context_instance=RequestContext(request))
    else:
        data_dict = {
            'from_date': from_date,
            'to_date': to_date,
            'search_trend': search_trend,
            'staff': False
        }
        return render_to_response("reports/feedback_report.html", data_dict, context_instance=RequestContext(request))

def feedback_report_list(from_date, to_date):
    pd_data = [['Day', 'Date', 'Feedback', 'Name', 'Email', 'Phone', 'City', 'Client']]
    dates = []
    diff = (to_date - from_date).days
    for i in range(0,diff+1):
        dates.append(from_date + timedelta(days=i))
    dates.reverse()
    for date in dates:
        day = day_name_of_date(date.weekday())
        feedbacks = Feedback.objects.filter(submitted_on__gte = date, submitted_on__lte = date + timedelta(days=1))
        for feedback in feedbacks:
            pd_data.append([day, date, feedback.feedback, feedback.name, feedback.email, feedback.phone, feedback.city, feedback.client.name])
    dict = {
        'list':pd_data,
        }
    return dict

def int_to_comma_seperated(i):
    string = str(i)
    if '.' in string:
        int_frac = string.split('.')
        int_part = splitthousands(int_frac[0])
        return int_part +'.'+ int_frac[1]
    else:
        int_part = splitthousands(string)
        return int_part 

def splitthousands(s, sep=','):  
    if len(s) <= 3:
        return s  
    return splitthousands(s[:-3], sep) + sep + s[-3:]
