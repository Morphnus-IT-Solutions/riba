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

from xlrd import open_workbook
from users.models import Subscription
import csv
from datetime import datetime, timedelta

count = 0
wb =  csv.reader(open('scripts/subscriptions_data/Deals Subscriber/subscribers_Tag_ACTIVE.csv',"rU"))
for row in wb:
    entry = str(row[0]).strip()
    a, created= Subscription.objects.get_or_create(email= entry, defaults={'tag':'active'})
    a.save()
    print count
    count += 1
    
        

wb =  csv.reader(open('scripts/subscriptions_data/Deals Subscriber/subscribers_Tag_ACTIVE(Bn).csv',"rU"))
count = 0
for row in wb:
    if count != 0:
        entry1 = str(row[0]).strip()
        bounced = str(row[1]).strip()
        print bounced
        bounced = datetime.strptime(bounced, '%Y-%m-%d').date()
        types = str(row[2]).strip()
        rsn = str(row[3]).strip()
     
        a, created= Subscription.objects.get_or_create(email= entry1, defaults={'bounced_on': bounced, 'subscription_type': types, 'reason':rsn, 'tag': 'active(bn)'})

        a.save()
    print count
    count += 1
    
        


wb =  csv.reader(open('scripts/subscriptions_data/Deals Subscriber/subscribers_Tag_NDNC.csv',"rU"))
count = 0
for row in wb:
    if count !=0:
        entry2 = str(row[0]).strip()
        unsubs = str(row[1]).strip()
        unsubs = datetime.strptime(unsubs, '%Y-%m-%d').date()
        
        a, created= Subscription.objects.get_or_create(email= entry2, defaults={'unsubscribed_on': unsubs, 'tag':'ndnc'})
        a.save()
    print count
    count += 1
    
        


wb =  csv.reader(open('scripts/subscriptions_data/FGSF/FGSF_Tag_ACTIVE.csv',"rU"))
count = 0
for row in wb:
    entry3 = str(row[0]).strip()
    a, created= Subscription.objects.get_or_create(email= entry3, defaults={'tag':'active'})
    if count != 0:
        a.save()
    print count
    count += 1
    
        

wb =  csv.reader(open('scripts/subscriptions_data/FGSF/FGSF_Tag_ACTIVE_(Bnc).csv',"rU"))
count = 0
for row in wb:
    if count != 0:
        entry4 = str(row[0]).strip()
        bounced2 = str(row[1]).strip()
        bounced2 = datetime.strptime(bounced2, '%Y-%m-%d').date()
        types2 = str(row[2]).strip()
        rsn2 = str(row[3]).strip()
     
        a, created= Subscription.objects.get_or_create(email= entry4, defaults={'bounced_on': bounced2,'subscription_type': types2, 'reason':rsn2, 'tag': 'active(bnc)'})
        a.save()
    print count
    count += 1
    
        

wb =  csv.reader(open('scripts/subscriptions_data/FGSF/FGSF_Tag_Ndnc.csv',"rU"))
count = 0
for row in wb:
    if count !=0:
        entry5 = str(row[0]).strip()
        unsubs2 = str(row[1]).strip()
        unsubs2 = datetime.strptime(unsubs2, '%Y-%m-%d').date()
        
        a, created= Subscription.objects.get_or_create(email= entry5, defaults={'unsubscribed_on': unsubs2, 'tag':'ndnc'})
        a.save()
    print count
    count += 1
    
        

wb =  csv.reader(open('scripts/subscriptions_data/BIGBAZAR_subs_aa.csv',"rU"))
count = 0
for row in wb:
    entry6 = str(row[0]).strip()
    a, created= Subscription.objects.get_or_create(phone= entry6, defaults={'tag':'active'})
    a.save()
    print count
    count += 1
    
        

wb =  csv.reader(open('scripts/subscriptions_data/BIGBAZAR_subs_ab.csv',"rU"))
count = 0
for row in wb:
    entry7 = str(row[0]).strip()
    a, created= Subscription.objects.get_or_create(phone= entry7, defaults={'tag':'active'})
    a.save()
    print count
    count += 1
    
        

wb = open("scripts/subscriptions_data/Subscribers_Tag_NDNC.txt")
count = 0
for row in wb:
    entry8 = str(row[0]).strip()
    a, created= Subscription.objects.get_or_create(phone= entry8, defaults={'tag':'NDNC'})
    a.save()
    print count
    count += 1
    
        
