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

from catalog.models import SellerRateChart, Tag, ProductTags, ProductVariant
from lists.models import List, ListItem

tag_name = 'itz'
promotion_name = 'itz_offer'
client_id = 5
list_id = 868#3010 #868

list = List.objects.get(id= list_id, type=promotion_name)

listitems = list.listitem_set.select_related('sku', 'sku__product').filter(status='active').order_by('sequence')
srcs = [l.sku for l in listitems]

tag = Tag.objects.filter(tag=tag_name)
if not tag:
    tag = Tag(tag=tag_name)
    tag.display_name = tag_name.capitalize()
    tag.save()
else:
    tag = tag[0]

previously_added_products = []
product_tags = ProductTags.objects.select_related('product').filter(type=promotion_name)
#print "product_tags---",product_tags[0].product

for pt in product_tags:
    previously_added_products.append(pt.product)

products_to_reindexed = []
products = []
variant_products = [s.product for s in srcs]
productvariants = ProductVariant.objects.select_related('blueprint', 'variant').filter(variant__in=variant_products)
variant_product_map = {}

for pv in productvariants:
    variant_product_map[pv.variant] = pv.blueprint

for product in variant_products:
    prod = product
    if product.type == 'variant':
        try:
            prod = variant_product_map[product]
        except KeyError:
            continue
    if prod not in products:
        products.append(prod)

for product in products:
    pt = ProductTags.objects.filter(type=promotion_name, product=product, tag=tag)
    if not pt:
        pt = ProductTags(type=promotion_name, product=product, tag=tag) # , sort_order = product.sequence
        pt.save()
        products_to_reindexed.append(product)
    else:
        pt = pt[0]
        if pt.product in previously_added_products:
            previously_added_products.remove(pt.product)
        products_to_reindexed.append(product) #####EXTRA ADDED

print "TOTAL NEW FOUND: ",len(products_to_reindexed)
product_tags = product_tags.filter(product__in=previously_added_products)
print "TOTAL OLD TAG TO BE INDEXED FOUND: ",product_tags.count()
for pt in product_tags:    
    products_to_reindexed.append(pt.product)
    print "DELETING PREVIOUSLY ADDED PRODUCT TAG:: %s" % pt
    pt.delete()

print "REINDEXING THE PRODUCTS ::: "
for product in products_to_reindexed:
    product.update_solr_index()

