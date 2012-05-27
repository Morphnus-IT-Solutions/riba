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

from categories.models import *
from catalog.models import *
from accounts.models import *

seller = Account.objects.get(name ='Micromax')
rateCharts = SellerRateChart.objects.filter(seller=seller)

for chart in rateCharts:
    product = chart.product
    brand = Brand.objects.get(name = 'Micromax')
    product.brand = brand
    product.save()
