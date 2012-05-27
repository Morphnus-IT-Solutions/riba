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
    ri, rie, oi, oi_a, oi_m, oi_p, oi_h = 0, 0, 0, 0, 0, 0, 0
    for rid in rids:
        if Order.objects.filter(reference_order_id=rid).exists():
            for order in Order.objects.filter(reference_order_id=rid):
                oi = oi+1
                pa_count = order.paymentattempt_set.filter(status='approved').count()
                if pa_count == 1:
                    oi_a = oi_a+1
                elif pa_count > 1:
                    oi_m = oi_m+1
                else:
                    if order.state == 'pending_order':
                        oi_p = oi_p+1
                    else:
                        oi_h = oi_h+1
        else:
            #print "[%09d] %s:no order found" % (ri, ref_id)
            rie = rie+1 # increment rid index exceptions (no order available available)
        ri = ri+1 # increment rid index
    print "FINDING:\n\tRIDs: %d (%d)\n\tOrders: %d\n\t\ta:%d m:%d p:%d h:%d" % (rie, ri, oi, oi_a, oi_m, oi_p, oi_h)


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
