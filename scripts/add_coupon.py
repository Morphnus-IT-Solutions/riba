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

from promotions.models import Coupon

for i in range(1,100):
    code = "CHPC%02d" % i
    coupon = Coupon()
    coupon.code = code
    coupon.status = 'active'
    coupon.use_when = 'manual'
    coupon.applies_to = 'order_total'
    coupon.discount_type = 'percentage'
    coupon.discount_value = i
    coupon.save()
