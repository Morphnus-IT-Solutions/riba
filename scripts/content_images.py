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

import shutil
path = "/home/apps/tinla/media/holii/images/pd/" 
dir_list = list(set(os.listdir(path)))
from catalog.models import *
from categories.models import *

for ele in dir_list:
    try:
        src = SellerRateChart.objects.get(article_id=ele, client__slug='future-bazaar')
        product= src.product
        product_type = product.product_type.type
        if not os.path.exists( "/home/ankush/Desktop/ankush/%s/%s" % (product_type,ele[-3:])):
            os.makedirs("/home/ankush/Desktop/ankush/%s/%s"%(product_type,ele[-3:]))
    except:
        pass

for ele in dir_list:
    try:
        src = SellerRateChart.objects.get(article_id=ele, client__slug='future-bazaar')
        product= src.product
        product_type = product.product_type.type
        dir_list1 = list(set(os.listdir("/home/ankush/Desktop/ankush/%s/"%product_type)))
        if ele[-3:] in dir_list1:
            os.makedirs("/home/ankush/Desktop/ankush/%s/%s/%s"%(product_type,ele[-3:],ele))
    except:
        pass

for ele in dir_list:
    try:
        src = SellerRateChart.objects.get(article_id=ele, client__slug='future-bazaar')
        product= src.product
        product_type = product.product_type.type
        try:
            imageversion = ImageVersion.objects.get(product=product)
            imageversion.version = imageversion.version+1
            imageversion.save()
        except:
            imageversion = ImageVersion()
            imageversion.version = 1
            imageversion.product = product
            imageversion.save()
        shutil.copytree("/home/apps/tinla/media/holii/images/pd/%s/"%ele,"/home/ankush/Desktop/ankush/%s/%s/%s/v%s/"%(product_type,ele[-3:],ele,imageversion.version))
    except SellerRateChart.DoesNotExist:
        pass
