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

from orders.models import Order
from integrations.fbapi.fbapiutils import PAYMENT_MODE_MAP

def main(rids):
    for rid in rids:
        print rid
        for order in Order.objects.filter(reference_order_id=rid):
            print "\t", order.id, order.payable_amount, order.state
            for pa in order.paymentattempt_set.all():
                print "\t\t", pa.id, pa.status, pa.amount
            print "---"
        print "===="


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] == ('-h' or '--help'):
        sys.stderr.write('Usage: %s <file-with-reference-order-id>\n' % sys.argv[0])
        sys.stderr.write('Reference ids in file must be one reference_order_id per line\n')
    else:
        fsock = open(sys.argv[1], 'r')
        reference_order_ids = [line.strip() for line in fsock.readlines()]
        reference_order_ids = [rid for rid in reference_order_ids if rid]
        fsock.close()
        main(reference_order_ids)
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 autoindent smartindent
