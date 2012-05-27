import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/') + 1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from catalog.models import SellerRateChart

for chart in SellerRateChart.objects.iterator():
    prod = chart.product
    if prod.status == 'available' or prod.status == 'Available':
        prod.status = 'active'
        chart.stock_status = 'instock'
    if prod.status in ['out_of_stock', 'unavailable', 'discontinued']:
        prod.status = 'deleted'
    prod.save()
    chart.save()
    prod.update_solr_index()
