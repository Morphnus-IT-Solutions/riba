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


from accounts.models import *
from catalog.models import *
from pricing.models import *
from decimal import Decimal

mb_phone_rate_charts = SellerRateChart.objects.filter(seller__name='Future Bazaar',product__category__id=1175,stock_status='instock',product__status='active')

#Insert entries in PriceList table
pl = PriceList(name='VISA', list_price_label='Market Price', offer_price_label='VISA Price')
pl.save()

pricelist = PriceList.objects.filter(name='VISA')
priceList = pricelist[0]
client = Client.objects.get(name='Future Bazaar')
domain = ClientDomain.objects.get(domain='stg.futurebazaar.com')
file = open('pricing_data.txt','w')

#2
file.write("Test Case 2\n\n")
temp = mb_phone_rate_charts[0]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")

file.write("========================================================\n\n\n")

#3
file.write("Test Case 3\n\n")
temp = mb_phone_rate_charts[1]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")

file.write("========================================================\n\n\n")
#4
file.write("Test Case 4\n\n")
temp = mb_phone_rate_charts[2]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")

file.write("========================================================\n\n\n")
#5
file.write("Test Case 5\n\n")
temp = mb_phone_rate_charts[3]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=2)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")

file.write("========================================================\n\n\n")
#6
file.write("Test Case 6\n\n")
temp = mb_phone_rate_charts[4]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=2)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#7
file.write("Test Case 7\n\n")
temp = mb_phone_rate_charts[5]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=2)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#8
file.write("Test Case 8\n\n")
temp = mb_phone_rate_charts[6]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=2)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#8-A
file.write("Test Case 8-A\n\n")
temp = mb_phone_rate_charts[7]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=2)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#9
file.write("Test Case 9\n\n")
temp = mb_phone_rate_charts[8]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1500'), offer_price=Decimal('750'))
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#10
file.write("Test Case 10\n\n")
temp = mb_phone_rate_charts[9]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('2500'), offer_price=Decimal('1250'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#11
file.write("Test Case 11\n\n")
temp = mb_phone_rate_charts[10]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3500'), offer_price=Decimal('1750'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#12
file.write("Test Case 12\n\n")
temp = mb_phone_rate_charts[11]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('2500'), offer_price=Decimal('1250'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1500'), offer_price=Decimal('750'))
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=2)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#13
file.write("Test Case 13\n\n")
temp = mb_phone_rate_charts[12]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3500'), offer_price=Decimal('1750'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1500'), offer_price=Decimal('750'))
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=2)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#14
file.write("Test Case 14\n\n")
temp = mb_phone_rate_charts[13]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('2500'), offer_price=Decimal('1250'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=2)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1500'), offer_price=Decimal('750'))
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#15
file.write("Test Case 15\n\n")
temp = mb_phone_rate_charts[14]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3500'), offer_price=Decimal('1750'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=2)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1500'), offer_price=Decimal('750'))
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#16
file.write("Test Case 16\n\n")
temp = mb_phone_rate_charts[15]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1500'), offer_price=Decimal('750'))
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#17
file.write("Test Case 17\n\n")
temp = mb_phone_rate_charts[16]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1500'), offer_price=Decimal('750'))
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#18

file.write("Test Case 18\n\n")
temp = mb_phone_rate_charts[17]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1500'), offer_price=Decimal('750'))
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#19
file.write("Test Case 19\n\n")
temp = mb_phone_rate_charts[18]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('2500'), offer_price=Decimal('1250'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#20
file.write("Test Case 20\n\n")
temp = mb_phone_rate_charts[19]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('2500'), offer_price=Decimal('1250'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#21
file.write("Test Case 21\n\n")
temp = mb_phone_rate_charts[20]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('2500'), offer_price=Decimal('1250'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#22
file.write("Test Case 22\n\n")
temp = mb_phone_rate_charts[21]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#23
file.write("Test Case 23\n\n")
temp = mb_phone_rate_charts[22]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#24
file.write("Test Case 24\n\n")
temp = mb_phone_rate_charts[23]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3500'), offer_price=Decimal('1750'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#25
file.write("Test Case 25\n\n")
temp = mb_phone_rate_charts[24]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('2500'), offer_price=Decimal('1250'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")

price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=2)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#26
file.write("Test Case 26\n\n")
temp = mb_phone_rate_charts[25]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3500'), offer_price=Decimal('1750'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('2500'), offer_price=Decimal('1250'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=2)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")

price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=2)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#27
file.write("Test Case 27\n\n")
temp = mb_phone_rate_charts[26]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3500'), offer_price=Decimal('1750'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1500'), offer_price=Decimal('750'))
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=2)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")

price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3000'), offer_price=Decimal('1500'), start_time='2011-06-11 00:00:00', end_time='2011-07-30 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=2)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#28
file.write("Test Case 28\n\n")
temp = mb_phone_rate_charts[27]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3500'), offer_price=Decimal('1750'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3500'), offer_price=Decimal('1750'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=2)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")

price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
file.write("========================================================\n\n\n")

#29
file.write("Test Case 29\n\n")
temp = mb_phone_rate_charts[28]
file.write("Rate Chart: ")
file.write(temp.__unicode__())

file.write("\n\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('3500'), offer_price=Decimal('1750'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
dlpl = DomainLevelPriceList(price=price, domain=domain, priority=1)
dlpl.save()
file.write("\tDomain Level Price List Entry: ")
file.write(dlpl.__unicode__())
file.write("\n")

price = Price(rate_chart=temp, price_list=priceList, price_type='timed', list_price=Decimal('5000'), offer_price=Decimal('2500'), start_time='2011-06-11 00:00:00', end_time='2011-06-20 00:00:00')
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=1)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")
price = Price(rate_chart=temp, price_list=priceList, price_type='fixed', list_price=Decimal('1000'), offer_price=Decimal('500'))
price.save()
clpl = ClientLevelPriceList(price=price, client=client, priority=2)
clpl.save()
file.write("\tClient Level Price List Entry: ")
file.write(clpl.__unicode__())
file.write("\n")

file.close()
