#!/usr/bin/python
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.htsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from promotions.models import *
from catalog.models import *
import xlrd

class UploadBundleOffers:
    def delete_previous_data(self):
        client = Client.objects.get(name = 'HomeTown')
        Bundle.objects.filter(offer__client= client).delete()
        Offer.objects.filter(client = client).delete()

    def get_offers(self):
        wb = xlrd.open_workbook(settings.HOME_PATH+'tinla/feeds/data/hometown/MYNMbundleoffertemplate.xls')
        client = Client.objects.get(name = 'HomeTown')
        for w in wb.sheet_names():
            s = wb.sheet_by_name(w)
            heading_map = {}
            for col in range(s.ncols):
               heading_map[s.cell(0,col).value.lower()] = col

            for row_num in range(1,s.nrows):
                row = s.row(row_num)
                offer_name = row[heading_map['name']].value
                offer_price = row[heading_map['offer price']].value
                tagline = row[heading_map['tagline']].value

                try:
                    add_offer = Offer.objects.get(name = offer_name, client = client)
                except Offer.DoesNotExist:
                    add_offer = Offer(name = offer_name, client = client, price_label = offer_price, description = tagline)
                    add_offer.save()
                    bundle_add = Bundle(offer = add_offer)
                    bundle_add.save()
                    for i in range(1,10):
                        if row[heading_map['sku'+ str(i)]].value:
                            if row[heading_map['sku'+ str(i)]].ctype in (2,3):
                                article_sku = str(int(row[heading_map['sku'+ str(i)]].value))
                            else:
                                article_sku = str(row[heading_map['sku'+ str(i)]].value)
                            try:
                                sellerRateChart = SellerRateChart.objects.get(sku = article_sku, seller__client = client)
                                bundle_add.primary_products.add(sellerRateChart)
                            except SellerRateChart.DoesNotExist:
                                continue 

if __name__ == '__main__':
    UploadObj = UploadBundleOffers()
    UploadObj.delete_previous_data()
    UploadObj.get_offers()



