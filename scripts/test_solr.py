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

from utils.solrutils import *

from analytics_orders.solr_queries import *
from datetime import datetime, timedelta, date
start_date = date(2012, 02, 26)
end_date = start_date
query = 'sku:2571682'
query += ' AND client_id:5'
fl = ['sku', 'listprice_26', 'offerprice_26', 'discount_26']
response = product_solr_search(query, fl)
results = response.results
for result in results:
    print "here"
    for key, value in result.items():
        print key, value

#for stat in stats:
#    print response[stat]
#stat = stats[0]
#resp = response[stat]
#rfa = resp['facets']
#skus = rfa[facet].keys()
#sku = skus[0]
#print rfa[facet][sku]
