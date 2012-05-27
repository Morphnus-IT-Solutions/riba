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

from affiliates.models import *

affiliate = Affiliate.objects.get(id=32)
count = 0
code_file = open('../paytm_codes.txt')
for code in code_file.readlines():
    count += 1
    code = code.strip()
    voucher = Voucher.objects.filter(code = code, affiliate = affiliate)
    if not voucher:
        voucher = Voucher()
        voucher.affiliate = affiliate
        print "CODE::",code, "COUNT::",count
        voucher.code = code
        voucher.uses = 1
        voucher.status = 'active'
        voucher.save()
    else:
        print "REPLICATED CODE::",code, "COUNT::",count
