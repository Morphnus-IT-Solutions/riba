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


from feedback.models import *
from notifications.notification import Notification
from notifications.email import Email as EmailAddress
from datetime import datetime, timedelta
from django.core.mail import send_mail, EmailMessage
import pyExcelerator


def email_excel_file(excel_header, excel_data):
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
                else:
                    docSheet1.write(row,i,str(list[i]))

    email_subject = "Future Bazaar Feedbacks" 
    email_body = "Please find attached the list of feedbacks received today."
    email_from = "Chaupaati Bazaar<lead@chaupaati.com>"
    email_to = "shaguniitb@gmail.com"
    email_bcc = ""

    mail_obj = EmailMessage(email_subject, email_body, email_from, email_to.split(','), email_bcc.split(','), None)
    mail_obj.attach('filename.xls', workBookDocument, 'text/xls')
    mail_obj.send()
    

    
#    response = HttpResponse(mimetype = "application/vnd.ms-excel")
#    response['Content-Disposition'] = 'attachmeant; filename=%s' % filename

#    subject = "Future Bazaar Feedbacks" 
#    email_body = "Please find attached the list of feedbacks received today."
#
#    email = EmailMessage(subject, email_body, 'shagun.iitb@yahoo.co.in', ['shaguniitb@gmail.com'])
#    email.attach('filename.xls', workBookDocument, 'text/xls')
#    email.send()
    
#    workBookDocument.save(response)
#    return response

def feedback_excel_list(date):
    from_date = date.date()
    to_date = from_date + timedelta(days=1)
    feedbacks = Feedback.objects.filter(submitted_on__gte = from_date, submitted_on__lte = to_date)
    pd_data = [["Feedback", "Name", "Email-id", "Phone", "City", "Client"]]
    for feedback in feedbacks:
        pd_data.append([feedback.feedback, feedback.name, feedback.email, feedback.phone, feedback.city, feedback.client])
    return pd_data

date = datetime.now() 
feedback_list = feedback_excel_list(date)
email_excel_file(feedback_list[0], feedback_list[1:])

