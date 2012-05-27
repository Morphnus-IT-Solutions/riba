import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('\\')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '\\')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('\\')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from catalog.models import *
from accounts.models import *

def copy(source_client, target_client):
    payment_modes = PaymentMode.objects.filter(client__id = source_client)
    for pm in payment_modes:
        p = PaymentMode()
        for field in pm._meta.fields:
            setattr(p,field.name,getattr(pm,field.name))
        p.id=None
        p.client_id = target_client
        p.save()

    payment_options = PaymentOption.objects.filter(payment_mode__client__id=source_client)
    for po in payment_options:
        p = PaymentOption()
        for field in po._meta.fields:
            setattr(p,field.name,getattr(po,field.name))
        p.id = None
        p.account = Account.objects.get(client = (Client.objects.get(id = target_client)))
        p.payment_mode = PaymentMode.objects.get(name = p.payment_mode.name,client__id = target_client)
        p.save()
