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
from analytics_deals.views import daily_deal_report_data
from analytics_utils.utils import get_excel_file

from django.template import Context, Template
from django.template.loader import get_template
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import smart_unicode, smart_str

from_date = (datetime.now()+timedelta(days=-1)).date()
to_date = (datetime.now()+timedelta(days=-1)).date()
filename = ROOT_FOLDER + '/daily_deal_report_' + str(from_date) + '.doc'
filename2 = ROOT_FOLDER + '/daily_deal_report_' + str(from_date) + '.xls'

data_dict = daily_deal_report_data(from_date, to_date, 'booked')
data = data_dict['list']
headings = data_dict['headings']
excel_data = [headings]
for data_entry in data:
    list_entry_one = [data_entry['day'], data_entry['date']]
    list_entry_two = [data_entry['total_sales']['count'], data_entry['total_sales']['value']]
    for line_entry in data_entry['entries']:
        excel_entry = list_entry_one + line_entry + list_entry_two
        excel_data.append(excel_entry)
workBookDocument = get_excel_file(excel_data[0], excel_data[1:])
workBookDocument.save(filename)
workBookDocument.save(filename2)

subject = 'Daily Deal Report - Booked orders'
message = 'Please find attached the daily deal report for yesterday. For more details, please access http://analytics.futurebazaar.com/category/deal_reports.'
msg_from = "Future Bazaar reports<support@futurebazaar.com>"
msg_to = ["Shagun.Jhaver@futuregroup.in", "shaguniitb@gmail.com", "dhimant.fb@gmail.com", "dhimantb@gmail.com", "Mary.Emmatty@futuregroup.in", "Dhimant.bakshi@futuregroup.in", "Sushil.patel@futuregroup.in", "Jatin.gada@futuregroup.in", "Priya.nayak@futuregroup.in", "Rajesh.chouhan@futuregroup.in", "Reena.chatnani@futuregroup.in", "Ricia.D'Souza@futuregroup.in", "Bhadrakshi.tanna@futuregroup.in", "Jaydeep.desai@futuregroup.in", "Rukmani.Iyengar@futuregroup.in", "Preeti.Vishnoi@futuregroup.in", "Kalyan.Das@futuregroup.in", "Suvarna.Chavan@futuregroup.in"]
em = EmailMessage(subject, message, msg_from, msg_to, [], None)
em.attach_file(filename)
em.attach_file(filename2)
em.send()
os.remove(filename)
os.remove(filename2)
        
