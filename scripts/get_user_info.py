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

from users.models import Profile
from integrations.fbapi import users, orders, fbapiutils
from orders.models import *


logins = '''9818833634
9899111556
jgeetharani@gmail.com
9869443499
9704879726
9969199134
ranumanna2011@gmail.com
9969199134
9464529568
niranarch@yahoo.com
rock90star@gmail.com
sandhoter.helpinghand@gmail.com
arun_k_saini@yahoo.co.in
8010784092
9322840824
9646449489
9810775637
meashishp@gmail.com
imcool.sacya@rediffmail.com
8976972597
meapoorva@gmail.com
9172403544
pdk2008@yahoo.com
dni2702@hotmail.com
babru56gupta@gmail.com
snehasis@gmx.com
babru56gupta@gmail.com
sugibabu@gmail.com
8010784092
jgeetharani@gmail.com
lakshyaaggarwal@yahoo.com
8010784092
arun1up@rediffmail.com
8010784092
raghav.1211@gmail.com
9894285684
9501866198
8010784092
sanjay_dce165@yahoo.co.in
aks005@yahoo.com
b2963418@klzlk.com
pavan6300@gmail.com
9766375134
mahipal.jain@wipro.com
9021190411
lovely.2905@gmail.com'''.split('\n')
logins = '''9818833634
9899111556
9894745686
9869443499
9704879726
9969199134
9088695334
9969199134
9888822827
9446531912
9464529568
9985146226
9868430314
8010784092
9322840824
9646449489
9810775637
9969879712
9076528113
8976972597
9870795436
9969879712
9840487392
8800815665
7814168572
9432120409
7814168572
9960746433
8010784092
9894745686
9911072488
8010784092
9868430314
8010784092
9930702849
9894285684
9501866198
8010784092
8802202591
9868430314
9985146226
9686422888
9766375134
9970170624
9021190411
9868430314'''.split('\n')

for login in logins:
    profile = None
    try:
        p = Phone.objects.get(phone=login)
        profile = p.user
    except Phone.DoesNotExist:
        try:
            e = Email.objects.get(email=login)
            profile = p.user
        except Email.DoesNotExist:
            pass

    if not profile:
        print 'no profile'
        continue

    o = Order.objects.filter(user=profile).exclude(state='cart').order_by('-id')
    if o:
        o = o[0]
        delivery_info = o.get_delivery_info()
    else:
        delivery_info = None
    if delivery_info:
        print login, delivery_info.address.name, profile.id
    else:
        print login, profile.full_name, profile.id

