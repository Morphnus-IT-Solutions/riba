import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.fgcsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
        sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
        sys.path.insert(1, PARENT_FOLDER)


from accounts.models import *

#1) Set all 29 payment modes for each client (For chaupaati)
#2) Set payment modes for all the clients
#3) Set domain payment options for all the domains

fb_client = Client.objects.get(id=5)
all_payment_modes = PaymentMode.objects.filter(client=fb_client)

print len(all_payment_modes)
clients = Client.objects.all()

for c in clients:
    for payment_mode in all_payment_modes:
        try:
            pm = PaymentMode.objects.get(client=c, code=payment_mode.code)
            print 'payment_mode already exists'
        except PaymentMode.DoesNotExist:
            pm = PaymentMode(
                name = payment_mode.name,
                code = payment_mode.code,
                client = c,
                is_grouped = payment_mode.is_grouped,
                group_code = payment_mode.group_code,
                group_name = payment_mode.group_name,
                service_provider = payment_mode.service_provider,
                validate_billing_info = payment_mode.validate_billing_info)
            pm.save()
            print 'Added payment mode'

fb_account = Account.objects.get(id=87)
all_payment_options = PaymentOption.objects.filter(account=fb_account).order_by('sort_order')
print len(all_payment_options)
sort_order = 100

all_accounts_list = Account.objects.filter(id__in=[78,87,88,89,90,91])

for acct in all_accounts_list:
    for po in all_payment_options:
        payment_mode_for_this_acct = PaymentMode.objects.get(code=po.payment_mode.code, client=acct.client)
        try:
            payment_option = PaymentOption.objects.get(account=acct, payment_mode=payment_mode_for_this_acct)
            print 'payment_option already exists'
        except PaymentOption.DoesNotExist:
            payment_option = PaymentOption(
                account = acct,
                payment_mode = payment_mode_for_this_acct,
                sort_order = sort_order,
                is_active = po.is_active,
                is_instant = po.is_instant,
                is_online = po.is_online,
                is_noninstant = po.is_noninstant,
                is_offline = po.is_offline)
            payment_option.save()
            sort_order += 1
            print 'payment_option added'

for c in clients:
    payment_options_client_level = PaymentOption.objects.filter(payment_mode__client=c)
    client_domains_per_client = ClientDomain.objects.filter(client = c)

    for option in payment_options_client_level:
        for domain in client_domains_per_client:
            try:
                dpo = DomainPaymentOptions.objects.get(client_domain=domain, payment_option=option)
            except DomainPaymentOptions.DoesNotExist:
                dpo = DomainPaymentOptions(client_domain=domain, payment_option=option, is_active=False)
                dpo.save()
            except DomainPaymentOptions.MultipleObjectsReturned:
                pass
