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

list_id = 3362
client_id = 5

skus = """2268872
2577045
2577182
2578570
2579155
2577047
2596781
2596786
2596791
2590058
2590057
2590320""".split("\n")[:-1]

msgs = []
count = 0

for s in skus:
    count += 1
    try:
        src = SellerRateChart.objects.get(sku=s, seller__client=client_id)
    except Exception,e:
        msgs.append("ERROR @ row: %s for SKU: %s -- %s" % (count, s, repr(e)))

count = 0
if msgs:
    for msg in msgs:
        print msg
else:
    for item in skus:
       try:
           src_id = SellerRateChart.objects.get(sku = item, seller__client=client_id)
           print item,"---->",src_id.id
       except:
           print item,"---->NOT FOUND"
