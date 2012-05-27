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

from catalog.models import *
from users.models  import *

email = Email.objects.get(email='dummy@yahoo.com')
print email.user.atg_username
emails = email.user.get_primary_emails()
print 'total',len(emails)
found = 0
notfound = 0
for e in emails:
    try:
        u = Profile.objects.get(atg_username=e.email)
        found += 1
    except Exception,e1:
        print 'exception',repr(e1)
        try:
            u = Profile.objects.get(user__user__username=e.email)
            found += 1
        except Exception,e2:
            print 'exception', repr(e1)
            notfound += 1

print 'found',found
print 'notfound',notfound
