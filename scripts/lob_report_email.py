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

from xlrd import open_workbook
from users.models import DailySubscription
import csv
import pyExcelerator
from datetime import datetime, timedelta, date
from analytics_utils.utils import get_excel_file, sum_it_up
from analytics_orders.reports import booked_range_qs, invoiced_range_qs
from analytics_deals.views import category_report_data

from django.template import Context, Template
from django.template.loader import get_template
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import smart_unicode, smart_str
from django.db.models import Sum


from_date = (datetime.now()+timedelta(days=-1)).date()
to_date = (datetime.now()+timedelta(days=-1)).date()
order_state = 'booked'
filename = ROOT_FOLDER + '/sales_report_' + str(from_date) + '.doc'

category_data, data_list = category_report_data(from_date, to_date, order_state)
category_list = [['Category-wise Product Performance']]
for cat_data in category_data:
    category = cat_data['category']
    if category == None:
        category = 'None'
    category_list.append([category] + [])
    category_list.append(['Top ' + str(category) + ' Products by Volume'])
    category_list += cat_data['volume'] + [[]]
    category_list.append(['Top ' + category + ' Products by Value'])
    category_list += cat_data['value'] + [[]]
excel_list = data_list + [[]] + category_list

workBookDocument = get_excel_file(excel_list[0], excel_list[1:])
workBookDocument.save(filename)

subject = 'Daily Sales Report - Booked (as per new Category tree)'
message = 'Please find attached the Daily Sales Report for yesterday. For more details, please access http://analytics.futurebazaar.com/category/category_report.'
msg_from = "Future Bazaar reports<support@futurebazaar.com>"
msg_to = ["Shagun.Jhaver@futuregroup.in", "shaguniitb@gmail.com", "dhimant.fb@gmail.com", "dhimantb@gmail.com", "Mary.Emmatty@futuregroup.in", "Dhimant.bakshi@futuregroup.in", "Sushil.patel@futuregroup.in", "Jatin.gada@futuregroup.in", "Priya.nayak@futuregroup.in", "Rajesh.chouhan@futuregroup.in", "Reena.chatnani@futuregroup.in", "Ricia.D'Souza@futuregroup.in", "Bhadrakshi.tanna@futuregroup.in", "Jaydeep.desai@futuregroup.in", "Rukmani.Iyengar@futuregroup.in", "Preeti.Vishnoi@futuregroup.in", "Kalyan.Das@futuregroup.in", "Suvarna.Chavan@futuregroup.in"]

em = EmailMessage(subject, message, msg_from, msg_to, [], None)
em.attach_file(filename)
em.send()
os.remove(filename)
