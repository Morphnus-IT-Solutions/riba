
#!/usr/bin/python

import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.htsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from users.models import Tab
tab_names = ['Catalog','User Experience-Reviews','User Experience-Feedback','User Experience-Content','User Experience-Site Propertie','Management-Notifications','Management-T&C','Management-Client Setup','Management-Profile','Management-User Rights','Payments-Risk','Payments-Marketplace Rec','Payments-Payouts','Payments-Recon Reports','Payments-Channel Settings','Payments-Option Settings','Marketing-Manage Promotions','Marketing-Manage Affiliates','Marketing-Payback','Marketing-Subscription','Sales-Orders','Category-Velocity','Category-Pricing','Category-Inventory','Category-Product Reviews','Category-Products','Category-Product Planner','Category-Deals','Fulfilment']
for name in tab_names:
    try:
        t = Tab.objects.get(tab_name=name, system='platform')
    except:
        t = Tab()
        t.tab_name = name
        t.system = 'platform'
        t.save()
