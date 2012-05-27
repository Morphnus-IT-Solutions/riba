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

from feeds.models import SyncEvent
from django.core.mail import EmailMessage
from catalog.models import Product, ProductTags, ProductVariant, Tag, SellerRateChart
from django.db.models import Q
from datetime import datetime, timedelta
import logging
import socket, struct, fcntl

log = logging.getLogger('events')

def compute(sync):
    _client_id = 5
    last_month = datetime.now() + timedelta(days=-30)
    # Get srcs of products created before 1 month
    new_rate_charts = SellerRateChart.objects.select_related('product', 'product__status').filter(product__is_online=True, seller__client=_client_id,\
                      product__created_on__gte=last_month).order_by("-product__created_on")[:200]
    new_products = []
    for src in new_rate_charts:
        new_products.append(src.product)
    # New arrivals products should be atleast 45 items
    if len(new_products) < 45:
        new_rate_charts = SellerRateChart.objects.select_related('product', 'product__status').filter(product__is_online=True,\
                          seller__client=_client_id).order_by("-product__created_on")[:200]
        new_products = []
        for src in new_rate_charts:
            new_products.append(src.product)

    # Create popular_deal tag, for indexing products into solr
    tag_type = 'new_arrivals'
    tag = Tag.objects.filter(tag=tag_type)
    if not tag:
        tag = Tag(tag=tag_type)
        tag.display_name = tag_type.capitalize()
        tag.save()
    else:
        tag = tag[0]
    products = []
    # variant_products contains product obj of {normal, variant} type
    # so replace variant products by variable 
    # to reindex in solr
    variant_products = new_products
    productvariants = ProductVariant.objects.select_related('blueprint', 'variant').filter(variant__in=variant_products)
    variant_product_map = {}
    for pv in productvariants:
        # get {variable : variant} mapping
        variant_product_map[pv.variant] = pv.blueprint
    for product in variant_products:
        prod = product
        if product.type == 'variant':
            try:
                # get corresponding variable of variant from variable:variant mapping
                prod = variant_product_map[product]
            except KeyError:
                continue
        if prod not in products:
            products.append(prod)
    # products list contains all products with type {variable, normal}
    product_ids_to_reindexed = []
    for product in products:
        try:
            pt = ProductTags.objects.select_related('product').get(type=tag_type, product=product, tag=tag)
        except ProductTags.DoesNotExist:
            pt = ProductTags()
            pt.type = tag_type
            pt.product = product  
            pt.tag = tag
            pt.save()
            # if product is not included in previous list then
            # then create ProductTag for it and reindex it 
        product_ids_to_reindexed.append(int(product.id))
    # Get previously indexed new arrivals from solr
    from utils.solrutils import solr_search
    q = 'tag_id:%s AND client_id:%s' % (tag.id, _client_id)
    params = {'rows':1000}
    solr_result = solr_search(q, fields='id', highlight=None, score=True, sort=None, sort_order="asc", operation='/select',\
                  active_product_query='', boost_query='', request=None, **params)

    indexed_new_arrivals = [int(res['id']) for res in solr_result.results]

    # ProductTags of (previously_indexed_new_arrivals - current_new_arrivals)
    # should to be removed
    new_arrivals_to_remove = set(indexed_new_arrivals) - set(product_ids_to_reindexed)
    product_ids_to_reindexed = set(product_ids_to_reindexed) - set(indexed_new_arrivals)
    log.info("New Arrivals ID:: %s" % product_ids_to_reindexed)
    sync.found = len(indexed_new_arrivals)
    sync.deletes = len(new_arrivals_to_remove)
    sync.add = len(product_ids_to_reindexed)
    sync.save()
    if not product_ids_to_reindexed:
        log.info("Found no new_arrivals")    
        return
    products_to_reindexed = Product.objects.filter(id__in=product_ids_to_reindexed)
    
    removed_new_arrivals = []
    for product_tag in ProductTags.objects.select_related('product').filter(product__in=new_arrivals_to_remove, tag=tag):
        removed_new_arrivals.append(product_tag.product)
        product_tag.delete()

    for product in products_to_reindexed:
        # Reindex:
        # 1) new product set (to add tag entry into solr)
        # 2) old tagged product set (to delete tag entry from solr)
        product.update_solr_index()
    for product in removed_new_arrivals:
        product.update_solr_index()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sockfd = sock.fileno()
SIOCGIFADDR = 0x8915

def get_ip(iface = 'eth0'):
    ifreq = struct.pack('16sH14s', iface, socket.AF_INET, '\x00'*14)
    try:
        res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
        return None
    ip = struct.unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)

if __name__ == '__main__':
    sync = SyncEvent()
    sync.account = 'Futurebazaar New Arrivals'
    sync.status = 'running'
    sync.started_at = datetime.now()
    sync.save()
    try:
        compute(sync)
        sync.status = 'finished'
    except Exception,e:
        sync.status = 'dead'
        import traceback
        import sys
        exc_info = sys.exc_info()
        st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        sync.stack_trace = st
        sync.status = 'dead'
        try:
            ip_address = get_ip('eth0')
            subject = 'Futurebazaar New Arrivals Failed from IP - %s' % ip_address
            body = st
            msg = EmailMessage(subject, body,
                "Future Bazaar Reports<lead@futurebazaar.com>",
                ['hemanth.goteti@futuregroup.in', 'krishna.raghavan@futuregroup.in', 'kishan.gajjar@futuregroup.in', 'fb-dev@futuregroup.in'])
            msg.send()
        except:
            pass
        print st
    sync.ended_at = datetime.now()
    sync.save()

