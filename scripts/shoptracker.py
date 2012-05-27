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

import urllib
from lxml import etree
from datetime import datetime,timedelta
from orders.models import *

class ShopTracker():
    COURIER = 'bluedart'
    TRACKING_URL = 'http://www.bluedart.com'
    URL = 'https://www.bluedart.com/servlet/RoutingServlet?handler=tnt&action=custawbquery&loginid=BOM02847&awb=ref&numbers=%s&format=xml&lickey=b3178928de990d1a8f8dfdbaa1233273&verno=1.3&scan=1'


    def fetch_info(self,order_id):
        fetch_url = ShopTracker.URL % order_id

        urllib.urlretrieve(fetch_url,'/tmp/bluedart_data.xml')
        file = '/tmp/bluedart_data.xml'
        info = {}
        xmldoc = etree.parse(file)
        fields = ['PickUpDate','Status','StatusType','StatusDate']
        for node in xmldoc.xpath("/ShipmentData"):
            childnodes = node.xpath("Shipment")
            for childnode in childnodes:
                info['WaybillNo'] = childnode.get('WaybillNo')
                for field in fields:
                    info[field] = ''
                    n = childnode.xpath(field)
                    if n and len(n) > 0 and n[0].text:
                        info[field] = n[0].text
        return info

    def update_info(self):
        try:
            seller_list = ['Amar Chitra Katha', 'IBD Books', 'IBD Magazines', 'Tinkle Comics']
            filter_date = datetime.today() - timedelta(days=20)
            orders = Order.objects.filter(payment_realized_on__gte=filter_date.date(),state='confirmed')
            for order in orders:
                print 'processing....', order.id
                order_items = OrderItem.objects.filter(order=order)
                for item in order_items:
                    if item.seller_rate_chart.seller.name in seller_list:
                        shipping_info = self.fetch_info(order.id)
                        print '@@@',shipping_info
                        if shipping_info['StatusType'] == 'NF':
                            continue
                        if shipping_info['PickUpDate']:
                            item.dispatched_on = datetime.strptime(shipping_info['PickUpDate'].strip(),'%d %B %Y')
                        if shipping_info['StatusType'] == 'DL':
                            if shipping_info['StatusDate']:
                                item.delivered_on = datetime.strptime(shipping_info['StatusDate'].strip(),'%d %B %Y')
                            item.state = 'delivered'
                        elif shipping_info['PickUpDate']:
                            item.state = 'shipped'
                        item.save()
                        try:
                            shipping_details = ShippingDetails.objects.get(order_item=item)
                        except ShippingDetails.DoesNotExist:
                            shipping_details = ShippingDetails()
                        shipping_details.order_item = item
                        shipping_details.tracking_no = shipping_info['WaybillNo']
                        shipping_details.tracking_url = ShopTracker.TRACKING_URL
                        shipping_details.courier = ShopTracker.COURIER
                        shipping_details.status = 'delivered' if shipping_info['StatusType'] == 'DL' else 'shipped'
                        shipping_details.shipper_status = shipping_info['Status']
                        shipping_details.save()
                    
        except Exception,e:
            print '@@@@',e

if __name__ == '__main__':
    s_tracker = ShopTracker()
    s_tracker.update_info()
