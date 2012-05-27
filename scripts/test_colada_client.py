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

from restapi import APIManager

jsonstr = "{\"shippingAddress\":\"gggg\",\"billingCurrencyCode\":\"\",\"billingPostalCode\":\"400001\",\"billingState\":\"26\",\"cardNumber\":\"1234567891234567\",\"billingCountry\":\"IN\",\"userAgent\":\"\",\"headerValue\":\"\",\"billingPhone\":\"1234567898\",\"shippingPostalCode\":\"400001\",\"billingEmail\":\"\",\"totalAmount\":\"1799.00\",\"shippingCity\":\"Mumbai\",\"orderId\":\"5034426782\",\"shippingPhone\":\"1234567898\",\"shippingCountry\":\"IN\",\"txnId\":\"\",\"cardType\":\"visa-card\",\"rmsRiskBox\":\"\",\"billingAddress\":\"gggg\",\"shippingName\":\"sss ggg\",\"shippingState\":\"26\",\"shippingEmail\":\"\",\"cardBillingName\":\"sss ggg\",\"productInformation\":\"1 X Speedo Womens Swimwear,Black\",\"profileId\":\"1116154\",\"ipAddress\":\"127.0.0.1\",\"billingCity\":\"Mumbai\"}"

jsonstr2 = "{\"shippingAddress\": \"a\", \"billingCurrencyCode\": \"\", \"billingPostalCode\": \"400006\", \"billingState\": \"13\", \"cardNumber\": \"1234567891234567\", \"billingCountry\": \"IN\", \"userAgent\": \"\", \"headerValue\": \"\", \"billingPhone\": \"8023570235\", \"shippingPostalCode\": \"400006\", \"billingEmail\": \"anubhav@anubhav.com\", \"totalAmount\": \"409.00\", \"shippingCity\": \"Mumbai\", \"orderId\": \"5036746074\", \"shippingPhone\": \"8023570235\", \"shippingCountry\": \"IN\", \"txnId\": \"\", \"cardType\": \"visa-card\", \"rmsRiskBox\": \"\", \"billingAddress\": \"a\", \"shippingName\": \"a a\", \"shippingState\": \"13\", \"shippingEmail\": \"\", \"cardBillingName\": \"a a\", \"productInformation\": \"1 X Sandisk 8 GB Pen Drive\", \"profileId\": \"217331108\", \"ipAddress\": \"127.0.0.1\", \"billingCity\": \"Mumbai\"}"

s = APIManager.ebs_check(jsonstr2);
print s

s = APIManager.getPromotionById(1950002);
print s

s = APIManager.getPromotionsByCouponCode(31, 'PAYBACK')
print s

