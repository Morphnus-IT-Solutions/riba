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
from orders.models import Order, OrderItem, OrderDailyCount, OrderCount, OrderCountByState
from catalog.models import Product, ProductTags, ProductVariant, Tag
from django.db.models import Q
from datetime import datetime, timedelta
import socket, struct, fcntl
import operator
import logging

log = logging.getLogger('events')

def min(a, b):
    if a < b:
        return a
    return b

def compute(sync):
    today = datetime.now()
    qs = Order.objects.using('tinla_slave').exclude(
        state__in = ('cart','unassigned_cart',
        'guest_cart','temporary_cart')).exclude(
        timestamp__lte = today + timedelta(days=-90)).order_by('timestamp')
    booked_numbers = {}
    paid_numbers = {}
    numbers = {}
    for order in qs:
        order_date = datetime(day=order.timestamp.day,
            month=order.timestamp.month,
            year=order.timestamp.year)
        if order_date not in numbers:
            numbers[order_date] = {}
        for order_item in OrderItem.objects.using(
            'tinla_slave').select_related(
            'rate_chart','product').filter(order=order):
            counts_for_day = numbers[order_date]
            p = order_item.seller_rate_chart.product
            if p not in counts_for_day:
                counts_for_day[p] = min(order_item.qty, 10) 
            else:
                counts_for_day[p] += min(order_item.qty, 10)
        if order.state == 'pending_order':
            booked_numbers[order_date] = numbers[order_date]
        elif order.state == 'confirmed':
            paid_numbers[order_date] = numbers[order_date]
    sorted_numbers = sorted(numbers.iteritems(), key=operator.itemgetter(0))
    for date, product_count_dict in sorted_numbers:
        for product,count in product_count_dict.iteritems():
            order_daily_count = None
            try:
                order_daily_count = OrderDailyCount.objects.get(
                    date = date,
                    product = product,
                    )
            except OrderDailyCount.DoesNotExist:
                rate_chart = product.primary_rate_chart()
                if not rate_chart:
                    continue
                order_daily_count = OrderDailyCount(
                    date = date,
                    product = product,
                    client = rate_chart.seller.client
                    )
            order_daily_count.order_count = count
            order_daily_count.save(using='default')

    
    qs = OrderDailyCount.objects.using('tinla_slave').exclude(
        date__lte = today + timedelta(days=-7)).order_by('date')
    # Store previous 7 days orders found 
    sync.found = qs.count()
    sync.save()
    numbers = {}
    counts_for_week = {}
    for count in qs:
        p = count.product
        if p not in counts_for_week:
            counts_for_week[p] = count.order_count
        else:
            counts_for_week[p] += count.order_count     
    
    for product, count in counts_for_week.iteritems():
        order_count = None
        try:
            order_count = OrderCount.objects.get(
                product = product
                )
        except OrderCount.DoesNotExist:
            rate_chart = product.primary_rate_chart()
            if not rate_chart:
                continue
            order_count = OrderCount(
                product = product,
                client = rate_chart.seller.client
                )
        order_count.order_count = count
        order_count.save(using='default')
    popular_pending_deals = set_count_for_state(booked_numbers, 'pending_order')
    popular_confirmed_deals = set_count_for_state(paid_numbers, 'confirmed')
    index_popular_deals(popular_pending_deals, popular_confirmed_deals)
    
def set_count_for_state(numbers, state):
    popular_products = []
    sorted_numbers = sorted(numbers.iteritems(), key=operator.itemgetter(0), reverse=True)
    previous_week = datetime.now() + timedelta(days=-7)
    order_count_obj = OrderCountByState.objects.filter(state=state).order_by('-id')
    last_count_id = 0
    if order_count_obj:
        last_count_id = order_count_obj[0].id
    has_sale = False
    for date, product_count_dict in sorted_numbers:
        if date < previous_week:
            break
        has_sale = True
        for product,count in product_count_dict.iteritems():
            order_count_state = None
            rate_chart = product.primary_rate_chart()
            if not rate_chart:
                continue
            order_count_state = OrderCountByState(
                state = state,
                product = product,
                client = rate_chart.seller.client,
                )
            order_count_state.order_count = count
            order_count_state.save(using='default')
            # If order count > 1 then product is in popular deals
            if count > 1:
                popular_products.append(product.id)
        log.info("ORDER COUNT BY STATE ADDED:: %s" % order_count_state)
    if has_sale:
        del_order_counts = OrderCountByState.objects.select_related("id").filter(id__lte=last_count_id, state=state)
        for order_count in del_order_counts:
            log.info("DELETING PREV ORDER COUNT:: %s" % (order_count))
            order_count.delete()
    return popular_products

def index_popular_deals(popular_pending_deals, popular_confirmed_deals, client_id=5):
    popular_products = popular_pending_deals + popular_confirmed_deals
    popular_products = Product.objects.filter(id__in=popular_products, is_online=True)
    if not popular_products:
        popular_orders = OrderCountByState.objects.select_related('product').filter(client=client_id,\
                         product__is_online=True).order_by('-order_count')[:200]
        popular_products = [order.product for order in popular_orders]
    # Create popular_deal tag, for indexing products into solr
    popular_type = 'popular_deals'
    tag = Tag.objects.filter(tag=popular_type)
    if not tag:
        tag = Tag(tag=popular_type)
        tag.display_name = popular_type.capitalize()
        tag.save()
    else:
        tag = tag[0]
    product_ids_to_reindexed = []
    products = []
    variant_products = popular_products
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
        try:
            pt = ProductTags.objects.select_related('product').get(type=popular_type, product=product, tag=tag)
        except ProductTags.DoesNotExist:
            pt = ProductTags()
            pt.type = popular_type
            pt.product = product  
            pt.tag = tag
            pt.save()
            product_ids_to_reindexed.append(int(product.id))

    from utils.solrutils import solr_search
    q = 'tag_id:%s AND client_id:%s' % (tag.id, client_id)
    params = {'rows':1000}
    solr_result = solr_search(q, fields='id', highlight=None, score=True, sort=None, sort_order="asc", operation='/select',\
                  active_product_query='', boost_query='', request=None, **params)

    indexed_popular_deals = [int(res['id']) for res in solr_result.results]

    popular_deals_to_remove = set(indexed_popular_deals) - set(product_ids_to_reindexed)
    product_ids_to_reindexed = set(product_ids_to_reindexed) - set(indexed_popular_deals)
    log.info("Popular Deals ID:: %s" % product_ids_to_reindexed)
    sync.found = len(indexed_popular_deals)
    sync.deletes = len(popular_deals_to_remove)
    sync.add = len(product_ids_to_reindexed)
    sync.save()
    if not product_ids_to_reindexed:
        log.info("Found no popular_deals")
        return

    products_to_reindexed = Product.objects.filter(id__in=product_ids_to_reindexed)

    removed_popular_deals= []
    for product_tag in ProductTags.objects.select_related('product').filter(product__in=popular_deals_to_remove, tag=tag):
        removed_popular_deals.append(product_tag.product)
        product_tag.delete()

    for product in products_to_reindexed:
        # Reindex:
        # 1) new product set (to add tag entry into solr)
        # 2) old tagged product set (to delete tag entry from solr)
        product.update_solr_index()
    for product in removed_popular_deals:
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
    sync.account = 'Tinla Compute Daily Order Count'
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
            subject = 'Tinla Compute Order Count Failed from IP - %s' % ip_address
            body = st
            msg = EmailMessage(subject, body,
                "Future Bazaar Reports<lead@futurebazaar.com>",
                ['hemanth.goteti@futuregroup.in', 'krishna.raghavan@futuregroup.in', 'kishan.gajjar@futuregroup.in', 'fb-dev@futuregroup.in'])
            msg.send()
        except:
            pass
    sync.ended_at = datetime.now()
    sync.save()
