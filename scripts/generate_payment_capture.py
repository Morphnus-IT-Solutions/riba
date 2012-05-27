import os
import sys
import tempfile

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from orders.models import *
import pyExcelerator

def main(reference_order_ids):
    wb = pyExcelerator.Workbook()
    ws = wb.add_sheet('final capture')
    ws.write(0,0,)
    PG_CODES = {'hdfc-card': 'HDPC',
                'hdfc-emi3': 'HDP3',
                'hdfc-emi6': 'HDP6',
                'hdfc-emi9': 'HDP9',
                'cc_avenue': 'CCAV'
                }

    approved_payments = []
    for reference_order_id in reference_order_ids:
        orders = Order.objects.filter(reference_order_id=reference_order_id)
        for order in orders:
            approved_payments.extend(order.paymentattempt_set.filter(status='approved'))

    row = 0 # row counter
    for approved_payment in approved_payments:
        ws.write(row, ord('A')-ord('A'), approved_payment.order.reference_order_id)
        ws.write(row, ord('D')-ord('A'), approved_payment.order.reference_order_id)
        ws.write(row, ord('F')-ord('A'), PG_CODES.get(approved_payment.gateway+approved_payment.emi_plan))
        ws.write(row, ord('N')-ord('A'), str(approved_payment.amount))
        ws.write(row, ord('O')-ord('A'), approved_payment.transaction_id)
        row += 1

    # Safely create a tempfile and close the file descriptor to save it as
    # empty file. This makes a persistent file on disk. We need to close the
    # descriptor, to be on the safer side because pyExcelerator works with
    # file's name and not file descriptor.
    fd, path = tempfile.mkstemp('.xls', 'PAYMENT_CAPTURE_', '/tmp/')
    os.close(fd)
    # Save Workbook to file
    wb.save(path)
    print "order infomation is saved at: %s" % path

import sys
if __name__ == "__main__":
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
