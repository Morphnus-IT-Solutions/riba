import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.nuezonesettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
	sys.path.insert(1, PARENT_FOLDER)

STATES_MAP = {'Andaman and Nicobar':'26','Andhra Pradesh':'01','Arunachal Pradesh':'02','Assam':'03','Bihar':'04','Chandigarh':'27','Chhaatisgarh':'33','Dadra and Nagar Hav.':'28','Daman and Diu':'29','Delhi':'30','Goa':'05','Gujarat':'06','Haryana':'07','Himachal Pradesh':'08','Jammu and Kashmir':'09','Jharkhand':'34','Karnataka':'10','Kerala':'11','Lakshadweep':'31','Madhya Pradesh':'12','Maharastra':'13','Maharashtra':'13','Manipur':'14','Meghalaya':'15','Mizoram':'16','Nagaland':'17','New Delhi':'30','Orissa':'18','Pondicherry':'32','Punjab':'19','Rajasthan':'20','Sikkim':'21','Tamil Nadu':'22','Tamilnadu':'22','Tripura':'23','Uttar Pradesh':'24','Uttaranchal':'35','West Bengal':'25'}

REGION_CODE = {'01':'S','02':'N','03':'E','04':'N','05':'W','06':'G','07':'N','08':'N','09':'N','10':'S','11':'S','12':'W','13':'W','14':'E','15':'E','16':'E','17':'E','18':'E','19':'N','20':'N','21':'E','22':'S','23':'E','24':'N','25':'E','26':'S','27':'N','28':'G','29':'W','30':'N','31':'S','32':'N','33':'N','34':'N','35':'N'}

from django.contrib.auth.models import *
from django.contrib.contenttypes.models import *
from users.models import *
from analytics.models import *
import pyExcelerator
import random
from orders.models import *
from django.core.mail import EmailMessage
from locations.models import *
import codecs

def customer_report(orders):
    if len(orders) > 0:
        #random_number = random.randrange(99999999,999999999)
        file_name = '/tmp/sap_customer_report-%s.txt' % datetime.now()
        file = open(file_name,'w')
        
        for order in orders:
            #Field-1 : Customer id
            profile_id = order.user.id
            padding = 10-(len(str(profile_id))+1)
            customer_id = "E"
            for i in range(0,padding):
                customer_id += "0"
            customer_id += str(profile_id)
            file.write("%s\t" % customer_id)
            
            #Field-2 to 7
            file.write("0101\t0101\t01\t")

            first_name = order.user.user.first_name
            last_name = order.user.user.last_name
            address_book = order.user.addressbook_set.all()
            if address_book:
                first_name = address_book[0].first_name
                last_name = address_book[0].last_name

            #Field-8: Last Name
            file.write("%s %s\t" % (first_name, last_name))

            #Field-9: First Name
            #file.write("%s\t" % first_name)

            #Fieild-10: Phone
            deliveryinfo = order.deliveryinfo_set.all()
            phones = None
            if deliveryinfo:
                phones = deliveryinfo[0].address.phone

            if not phones:
                phones = order.user.get_primary_phones()
                if phones:
                    phones = phones[0]
            
            file.write("%s\t" % phones)

            address, address1, address2 = "", "", ""
            if deliveryinfo:
                #address = str(unicode(deliveryinfo[0].address.address.strip(codecs.BOM_UTF8), 'utf-8'))
                address = deliveryinfo[0].address.address.encode('ascii','ignore')
                #unicode(q.content.strip(codecs.BOM_UTF8), 'utf-8')
                if address:
                    address = address.replace('\r',' ')
                    address = address.replace('\t',' ')
                    address = address.split('\n')
                    if len(address) > 1:
                        address1 = str(address[0])
                        for item in address[1:]:
                            address2 += str(item) + ','
                        address2 = address2[:(len(address2)-1)]
                    else:
                        address = str(address[0]).split(',')
                        if len(address) > 1:
                            address1 = str(address[0])
                            for item in address[1:]:
                                address2 += str(item) + ','
                            address2 = address2[:(len(address2)-1)]
                        else:
                            address1 = str(address[0])
                            address2 = str(address[0])

            file.write("%s\t%s\t" % (address1, address2))

            #Field-12: City
            city = ''
            if deliveryinfo:
                city = deliveryinfo[0].address.city.name
            file.write("%s\tIN\t" % city)

            #Field-13: Region Code -- To be done
            region_code = ''
            if deliveryinfo:
                state = deliveryinfo[0].address.state.name
                if state == '13':
                    region_code = state
                else:
                    region_code = STATES_MAP[state]
            file.write("%s\t58\tEN\t" % region_code)
            
            #Field-11: Pincode
            deliveryinfo = order.deliveryinfo_set.all()
            pincode = ''
            if deliveryinfo:
                pincode = deliveryinfo[0].address.pincode
            file.write("%s\t" % pincode)



#            #Field-13: Region Code
#            region_code = ''
#            if deliveryinfo:
#                state = deliveryinfo[0].address.state.name
#                region_code = STATES_MAP[state]
#            file.write("%s\t" % region_code)

            #Zone
            zone = REGION_CODE[region_code]
            file.write("%s\t" % zone)


            #Field-14 to 16
            file.write("CFR\tCosts and Freight\t")

            #Payment mode
            if order.payment_mode == 'cod':
                file.write("0038\n")
            else:
                file.write("0001\n")

        file.close()

        return file_name

def sales_report(orders):
    if len(orders) > 0:
        #random_number = random.randrange(99999999,999999999)
        file_name = '/tmp/sap_sales_report-%s.txt' % datetime.now()
        file = open(file_name,'w')
        
        for order in orders:
            #Row-1
            file.write("H\tT00%s\tZTIL\t0101\t01\t00\t6583\n" % order.reference_order_id[4:])

            #Row-2
            profile_id = order.user.id
            padding = 10-(len(str(profile_id))+1)
            customer_id = "E"
            for i in range(0,padding):
                customer_id += "0"
            customer_id += str(profile_id)
            file.write("P\tSP\t%s\n" % customer_id)

            #Row-3
            deliveryinfo = order.deliveryinfo_set.all()
            file.write("P\tSH\t%s\tA\n" % customer_id)
#            file.write("P\tSH\tE000000001\tA\t%s\t" % order.user.full_name)
#            address, address1, address2 = "", "", ""
#            if deliveryinfo:
#                #address = str(unicode(deliveryinfo[0].address.address.strip(codecs.BOM_UTF8), 'utf-8'))
#                address = deliveryinfo[0].address.address.encode('ascii','ignore')
#                #unicode(q.content.strip(codecs.BOM_UTF8), 'utf-8')
#                if address:
#                    address = address.split('\n')
#                    if len(address) > 1:
#                        address1 = str(address[0])
#                        for item in address[1:]:
#                            address2 += str(item) + ','
#                    else:
#                        address = str(address[0]).split(',')
#                        if len(address) > 1:
#                            address1 = str(address[0])
#                            for item in address[1:]:
#                                address2 += str(item) + ','
#                        else:
#                            address1 = str(address[0])
#                            address2 = str(address[0])
#
#            file.write("%s\t%s\t" % (address1, address2))
#
#            city = ''
#            if deliveryinfo:
#                city = str(deliveryinfo[0].address.city.name)
#            file.write("%s\t" % city)
#
#
#            #Field-13: Region Code -- To be done
#            region_code = ''
#            if deliveryinfo:
#                state = deliveryinfo[0].address.state.name
#                region_code = STATES_MAP[state]
#            file.write("%s\t" % region_code)
#
#            pincode = ''
#            if deliveryinfo:
#                pincode = str(deliveryinfo[0].address.pincode)
#            file.write("IN\t%s\t" % pincode)
#            
#            phones = order.user.get_primary_phones()
#            phone1, phone2 = "", ""
#            if phones:
#                if len(phones) >1:
#                    phone1 = str(phones[0])
#                    phone2 = str(phones[1])
#                else:
#                    phone1 = str(phones[0])
#                    phone2 = str(phones[0])
#            file.write("%s\t%s\n" % (phone1, phone2))         

            coupon_discount = Decimal('0')
            delivery_discount = Decimal('0')
            if order.coupon:
                if order.coupon.applies_to in ['order_total', 'product_offer_price']:
                    coupon_discount = Decimal(order.coupon_discount)
                if order.coupon.applies_to == 'order_shipping_charge':
                    delivery_discount = Decimal(self.coupon_discount)

            count = 1
            all_orderitems = order.orderitem_set.all()
            print order.id
            print all_orderitems
            no_of_orderitems = len(all_orderitems)

            remaining_coupon_discount = coupon_discount
            remaining_delivery_discount = delivery_discount

            for oi in all_orderitems:
                order_count = str(count*10)
                file.write("D\t%s\t%s\t8796\t%s\t" % (order_count, oi.seller_rate_chart.article_id, str(oi.qty)))
                shipping_duration = oi.seller_rate_chart.shipping_duration
                if not shipping_duration:
                    shipping_duration = '10'
                shipping_duration = int(str(shipping_duration))
                #delivery_date = oi.order.timestamp #+ timedelta(days=shipping_duration)
                delivery_date = oi.order.timestamp + timedelta(days=1)
                file.write("%s\n" % delivery_date.strftime('%d.%m.%Y'))

                file.write("C\t%s\tYKP0\t%s\n" % (order_count, oi.sale_price))

                file.write("C\t%s\tZTPB\t%s\n" % (order_count, '0'))#Payback discount
               
                oi_coupon_discount = Decimal('0')
                if coupon_discount:
                    if count < no_of_orderitems:
                        oi_coupon_discount = int((oi.sale_price*oi.qty*coupon_discount)/(oi.order.payable_amount))
                        remaining_coupon_discount = coupon_discount - Decimal(str(oi_coupon_discount))
                        oi_coupon_discount = ("%.1f" % oi_coupon_discount).replace('.0','')
                    else:
                        oi_coupon_discount = remaining_coupon_discount 
                        oi_coupon_discount = ("%.1f" % oi_coupon_discount).replace('.0','')
                     
                file.write("C\t%s\tZTCD\t%s\n" % (order_count, oi_coupon_discount))#Coupon discount
                
                oi_cashback_amount = ("%.1f" % oi.cashback_amount).replace('.0','')
                file.write("C\t%s\tZTCB\t%s\n" % (order_count, oi_cashback_amount))
                
                oi_shipping_charges = ("%.1f" % oi.shipping_charges).replace('.0','')
                file.write("C\t%s\tZTDC\t%s\n" % (order_count, oi_shipping_charges))

                oi_delivery_discount = Decimal('0')
                if delivery_discount:
                    if count < no_of_orderitems:
                        oi_delivery_discount = int((oi.sale_price*oi.qty*delivery_discount)/(oi.order.payable_amount))
                        remaining_delivery_discount = delivery_discount - Decimal(str(oi_delivery_discount))
                        oi_delivery_discount = ("%.1f" % oi_delivery_discount).replace('.0','')
                    else:
                        oi_delivery_discount = remaining_delivery_discount 
                        oi_delivery_discount = ("%.1f" % oi_delivery_discount).replace('.0','')
                
                file.write("C\t%s\tZTDD\t%s\n" % (order_count, oi_delivery_discount))#Delivery Discount
                count += 1

            first_name = order.user.user.first_name
            last_name = order.user.user.last_name
            address_book = order.user.addressbook_set.all()
            if address_book:
                first_name = address_book[0].first_name
                last_name = address_book[0].last_name
            
            file.write("A\t%s\t%s %s\t" % (customer_id, first_name, last_name))
            address, address1, address2 = "", "", ""
            if deliveryinfo:
                #address = str(unicode(deliveryinfo[0].address.address.strip(codecs.BOM_UTF8), 'utf-8'))
                address = deliveryinfo[0].address.address.encode('ascii','ignore')
                #unicode(q.content.strip(codecs.BOM_UTF8), 'utf-8')
                if address:
                    address = address.replace('\t',' ')
                    address = address.replace('\r',' ')
                    address = address.split('\n')
                    if len(address) > 1:
                        address1 = str(address[0])
                        for item in address[1:]:
                            address2 += str(item) + ','
                        address2 = address2[:(len(address2)-1)]
                    else:
                        address = str(address[0]).split(',')
                        if len(address) > 1:
                            address1 = str(address[0])
                            for item in address[1:]:
                                address2 += str(item) + ','
                            address2 = address2[:(len(address2)-1)]
                        else:
                            address1 = str(address[0])
                            address2 = str(address[0])

            file.write("%s\t%s\t" % (address1, address2))

            city = ''
            if deliveryinfo:
                city = str(deliveryinfo[0].address.city.name)
            file.write("%s\t" % city)


            #Field-13: Region Code -- To be done
            region_code = ''
            if deliveryinfo:
                state = deliveryinfo[0].address.state.name
                if state == '13':
                    region_code = '13'
                else:
                    region_code = STATES_MAP[state]
            file.write("%s\t" % region_code)

            pincode = ''
            if deliveryinfo:
                pincode = str(deliveryinfo[0].address.pincode)
            file.write("IN\t%s\t" % pincode)
           

            phones = None
            if deliveryinfo:
                phones = deliveryinfo[0].address.phone

            if not phones:
                phones = order.user.get_primary_phones()
                if phones:
                    phones = phones[0]

            file.write("%s\n" % phones) 
#            phones = order.user.get_primary_phones()
#            phone1, phone2 = "", ""
#            if phones:
#                if len(phones) >1:
#                    phone1 = str(phones[0])
#                    phone2 = str(phones[1])
#                else:
#                    phone1 = str(phones[0])
#                    phone2 = str(phones[0])
#            file.write("%s\t%s\n" % (phone1, phone2)) 

        file.close()

        return file_name

if __name__ == '__main__':
    from datetime import datetime, timedelta
    c_file_name, s_file_name = None, None
    today = datetime.now()
    today = datetime.strptime(today.strftime("%Y-%m-%d") + " 14:00","%Y-%m-%d %H:%M")
    yesterday = datetime.strptime(today.strftime("%Y-%m-%d") + " 08:00","%Y-%m-%d %H:%M")
    
    #Confirmed orders report
    orders = Order.objects.using('tinla_slave').filter(state='confirmed', 
        modified_on__gte=yesterday, modified_on__lt=today, client=12)

    #orders = Order.objects.filter(reference_order_id__in=['10125513159'])
    #print orders

    if orders:
        c_file_name = customer_report(orders)
        s_file_name = sales_report(orders)
        #print c_file_name
        #print s_file_name

    subject = 'Customer and Sales confirmed order report of %s to %s' % (yesterday, today)
    body = 'PFA Customer and Sales confirmed order Report of %s to %s' % (yesterday, today)

    msg = EmailMessage(subject, body, 'report@ezoneonline.in',
        ['suhas.kajbaje@futuregroup.in','Joe.Kochitty@futuregroup.in','Nikhat.Patel@futuregroup.in','Zishaan.Hayath@futuregroup.in','Prashanth.Thiruvaipati@futuregroup.in','saumil.dalal@futuregroup.in','Nirmal.Mekala@futuregroup.in'],
        '',None)  
    if c_file_name:
        data1 = open(c_file_name, 'rb').read()
        msg.attach('customer-%s.txt' % today, data1)
    
    if s_file_name:
        data2 = open(s_file_name, 'rb').read()
        msg.attach('sales-%s.txt' % today, data2)
    
    if c_file_name or s_file_name:
        msg.send()

    #Cancelled orders report
    orders = Order.objects.using('tinla_slave').filter(state='cancelled', 
        modified_on__gte=yesterday, modified_on__lt=today, client=12)

    #orders = Order.objects.filter(reference_order_id__in=['10125513159'])
    #print orders

    if orders:
        c_file_name = customer_report(orders)
        s_file_name = sales_report(orders)
        #print c_file_name
        #print s_file_name

    subject = 'Customer and Sales cancelled order report of %s to %s' % (yesterday, today)
    body = 'PFA Customer and Sales cancelled order Report of %s to %s' % (yesterday, today)

    msg = EmailMessage(subject, body, 'report@ezoneonline.in',
        ['Joe.Kochitty@futuregroup.in','Prashanth.Thiruvaipati@futuregroup.in','Kuldeep.khare@futuregroup.in','Bharat.pawar@futuregroup.in'],
        '',None)  
    if c_file_name:
        data1 = open(c_file_name, 'rb').read()
        msg.attach('customer-%s.txt' % today, data1)
    
    if s_file_name:
        data2 = open(s_file_name, 'rb').read()
        msg.attach('sales-%s.txt' % today, data2)
    
    if c_file_name or s_file_name:
        msg.send()
