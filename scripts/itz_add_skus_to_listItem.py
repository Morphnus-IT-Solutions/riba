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

from lists.models import List, ListItem
from catalog.models import SellerRateChart
from franchise.models import * 

list_type = 'itz_offer'
client_id = 5
list = List.objects.get(type=list_type)

skus = """
""".split("\n")

msgs = []
count = 0

for s in skus:
    count += 1
    s = s.strip()
    if s:
        try:
            src = SellerRateChart.objects.get(sku=s, seller__client=client_id)
        except Exception,e:
            msgs.append("ERROR @ row: %s for SKU: %s -- %s" % (count, s, repr(e)))

'''
count = 0
if msgs:
    for msg in msgs:
        print msg
else:
    for s in skus:
        if s:
            s = s.strip()
            count += 1
            listitem = ListItem(list=list)
            src = SellerRateChart.objects.get(sku=s, seller__client=client_id)
            listitem.sku = src
            listitem.sequence = count
            listitem.status = 'active'
            listitem.save()
            msgs.append("SKU added: %s" % s)
    for msg in msgs:
        print msg

'''