import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

#from django.contrib.auth.models import *
#from django.contrib.contenttypes.models import *
from cs.models import *
import pyExcelerator
import random
from datetime import datetime, timedelta
from django.core.mail import EmailMessage

def response_report(queryset):
    if len(queryset) > 0:

        response = queryset[0]
        from django.core.exceptions import PermissionDenied
        from django.template import Context, Template
        
        field_headers = ['Interaction Id','Order Id','High Priority','State','Status','Created On','Campaign', 'Brand',
            'Phone','Name','Email','Address','City','Province','Country','Pin','User','Message','Medium',
            'Open','Attempts','Connections','Last Call','Last Called By','Next Call','Agent','WIP','Closed','UnSatisfactory']

        ax = []
        wb = pyExcelerator.Workbook()
        ws = wb.add_sheet('data')
        ws.write(0,0,)
        col = 0
        for header  in field_headers:
            ws.write(0,col,header)
            col +=1
        row = 1
        for response in queryset:
            ws.write(row,0,str(response.id))
            ws.write(row,1,unicode(response.order_id))
            ws.write(row,2,'True' if response.high_priority else 'False')
            ws.write(row,3,response.state)
            ws.write(row,4,response.status.name)
            ws.write(row,5,str(response.created_on))
            ws.write(row,6,response.campaign.name)
            ws.write(row,7,response.brand.name)
            ws.write(row,8,response.phone)
            ws.write(row,9,response.name)
            ws.write(row,10,response.email)
            ws.write(row,11,response.address)
            ws.write(row,12,response.city)
            ws.write(row,13,response.province)
            ws.write(row,14,response.country)
            ws.write(row,15,response.pin)
            ws.write(row,16,response.user.name)
            ws.write(row,17,response.message)
            ws.write(row,18,response.medium)
            ws.write(row,19,'False' if response.closed else 'True')
            ws.write(row,20,str(response.attempts))
            ws.write(row,21,str(response.connections))
            ws.write(row,22,str(response.last_call) or '')
            try:
                if response.last_called_by:
                    ws.write(row,23,response.last_called_by.name or '')
            except:
                ws.write(row,23, '')

            ws.write(row,24,str(response.next_call) or '')
            try:
                #ws.write(row,25,response.borrowed_by.name)
                agent = unicode(getattr(response,'agent')())
                ws.write(row,25,agent)
            except:
                ws.write(row,25,'')
            ws.write(row,26,'True' if response.wip else 'False')
            ws.write(row,27,'True' if response.closed else 'False')
            ws.write(row,28,'True' if response.unsatisfactory else 'False')
            row +=1
        
        random_number = random.randrange(99999999,999999999)
        file_name = '/tmp/responsereport%s.xls' % random_number
        wb.save(file_name)
        return file_name

    else:

        field_headers = ['Interaction Id','Order Id','High Priority','State','Status','Created On','Campaign', 'Brand',
            'Phone','Name','Email','Address','City','Province','Country','Pin','User','Message','Medium',
            'Open','Attempts','Connections','Last Call','Last Called By','Next Call','Agent','WIP','Closed','UnSatisfactory']

        ax = []
        wb = pyExcelerator.Workbook()
        ws = wb.add_sheet('data')
        ws.write(0,0,)
        col = 0
        for header  in field_headers:
            ws.write(0,col,header)
            col +=1
        row = 1
        
        random_number = random.randrange(99999999,999999999)
        file_name = '/tmp/responsereport%s.xls' % random_number
        wb.save(file_name)
        return file_name

if __name__ == '__main__':
    # generate daily report
    today = datetime.now()
    yesterday = today + timedelta(days=-1)
    today = today.strftime("%Y-%m-%d")
    yesterday = yesterday.strftime("%Y-%m-%d")
    responses = Response.objects.filter(created_on__gte=yesterday,created_on__lt=today)
    dailyresponse_file_name = response_report(responses)
    responses = Response.objects.filter(next_call__gte=yesterday,next_call__lt=today)
    dailycallbackresponses_file_name = response_report(responses)
   
#    print 'yesterday: ',yesterday, 'today:', today
   
    # generate monthly report
    today = datetime.now()
    yesterday = today + timedelta(days=-1)
    if(today.day == 1):
        startofprevmonth = today + timedelta(days =- yesterday.day)
        today = today.strftime("%Y-%m-%d")
        startofprevmonth = startofprevmonth.strftime("%Y-%m-%d")
        responses = Response.objects.filter(created_on__gte=startofprevmonth,created_on__lt=today)
        monthlyresponse_file_name = response_report(responses)
        responses = Response.objects.filter(next_call__gte=startofprevmonth,next_call__lt=today)
        monthlycallbackresponses_file_name = response_report(responses)
   
#    print 'monthstart:', startofprevmonth, 'today:', today
   
   # send email
    subject = 'Response and Callback report of %s' % yesterday
    body = 'Response and Callback Report of %s' % yesterday
    msg = EmailMessage(subject, body, 'report@chaupaati.com',
        ['hemanth@chaupaati.com','rajesh.kaushik2@futuregroup.in','millicent.parab@futuregroup.in','Goldie.Creado@futuregroup.in', 'Grishma.talati@futuregroup.in', 'Mitesh.sarvaiya@futuregroup.in'],
        '',None)
    data1 = open(dailyresponse_file_name, 'rb').read()
    data2 = open(dailycallbackresponses_file_name, 'rb').read()
    msg.attach('dailyresponse%s.xls' % yesterday, data1)
    msg.attach('dailycallback%s.xls' % yesterday, data2)
   
    today = datetime.now()
    if(today.day == 1):
        data3 = open(monthlyresponse_file_name, 'rb').read()
        data4 = open(monthlycallbackresponses_file_name, 'rb').read()
        msg.attach('monthlyresponse%s.xls' % startofprevmonth, data3)
        msg.attach('monthlycallback%s.xls' % startofprevmonth, data4)
    
    msg.send()
