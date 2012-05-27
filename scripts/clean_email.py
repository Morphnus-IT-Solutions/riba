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

from users.models import Email
from utils.utils import get_cleaned_email


e = Email.objects.all()
clean_email_list = []
count = 0
for d in e:
    try:
        clean_email = get_cleaned_email(d.email)
        if clean_email and clean_email not in clean_email_list:
            d.cleaned_email = clean_email
            d.save(using="default")
            clean_email_list.append(clean_email)
            print "%s. Cleaned Email : %s -> %s" % (count, d.email, d.cleaned_email)
            count += 1
        else:
            d.cleaned_email = None
            d.save(using="default")
            print "Duplicate email: %s" % d.email
    except Exception, e:
        print "%s for %s" % (e, d.email)
