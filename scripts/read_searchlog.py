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

import re
import os
from datetime import datetime
from analytics.models import *
from users.models import *
date = datetime.today().strftime('%Y-%m-%d')
os.system("cat /home/chaupaati/tinla/logs/search.log | grep '%s' > /tmp/search-today.log" % date)
f = open('/tmp/search-today.log')
lines = f.readlines()
for line in lines:
    m =re.search(r"(.*) - search - INFO - User: (.*), Domain: (.*), User Agent: (.*), Keywords: (.*), total_results: (.*)",line)
    if m:
        sl=SearchLog()
        sl.date=m.groups()[0].split(',')[0]
        sl.domain=m.groups()[2]
        sl.user_agent=m.groups()[3]
        sl.keyword=m.groups()[4]
        sl.total_results=m.groups()[5]
        if m.groups()[1] and m.groups()[1] != 'None':
                try:
                    profile=Profile.objects.get(user=m.groups()[1])
                    sl.user=profile
                except:
                        pass
        sl.save()

    if not m:
        m =re.search(r"(.*) - search - INFO - Domain: (.*), User Agent: (.*), Keywords: (.*), total_results: (.*)",line)
        if m:
            sl=SearchLog()
            sl.date=m.groups()[0].split(',')[0]
            sl.domain=m.groups()[1]
            sl.user_agent=m.groups()[2]
            sl.keyword=m.groups()[3]
            sl.total_results=m.groups()[4]
            sl.save()           

    if not m:
        m =re.search(r"(.*) - search - INFO - User Agent: (.*), Keywords: (.*), total_results: (.*)",line)
        if m:
            sl=SearchLog()
            sl.date=m.groups()[0].split(',')[0]
            sl.user_agent=m.groups()[1]
            sl.keyword=m.groups()[2]
            sl.total_results=m.groups()[3]
            sl.save()           
    if not m:
        m =re.search(r"(.*) - search - INFO - Keywords: (.*), total_results: (.*)",line)
        if m:
            sl=SearchLog()
            sl.date=m.groups()[0].split(',')[0]
            sl.keyword=m.groups()[1]
            sl.total_results=m.groups()[2]
            sl.save()          
    if not m:
        m =re.search(r"(.*) - search - INFO - Domain: (.*), Keywords: (.*), total_results: (.*)",line)
        if m:
            sl=SearchLog()
            sl.date=m.groups()[0].split(',')[0]
            sl.domain=m.groups()[1]
            sl.keyword=m.groups()[2]
            sl.total_results=m.groups()[3]
            sl.save()          
            

