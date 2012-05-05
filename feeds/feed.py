import urllib2
from categories.models import Category,Feature
from catalog.models import Brand, Product, SellerRateChart,ProductFeatures, ProductVariant,ProductImage, BundleProducts, Tag, ProductTags
from accounts.models import Account
from utils import htmlutils
from feeds.models import CategoryMapping, BrandMapping, BrandBlackList, CategoryBlackList, SKUBlackList, SkuTypeProductTypeMapping, ExtPricelist
from feeds.models import SyncEvent, SyncEventProductMapping, SyncEventRateChartMapping, FeatureMapping
from pricing.models import *
from feeds import feedutils
import logging
from datetime import datetime
from django.template.defaultfilters import slugify, striptags
from django.utils import simplejson
from decimal import Decimal
import copy
from django.core.mail import EmailMessage
from django.db.models import Q
from django import db
from django.conf import settings
import socket, struct, fcntl

log = logging.getLogger('feeds')

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


class Feed:
    _brand_cache = {}
    update_description = False
    only_add = False
    download_images = True

    def __init__(self,update_description=False,only_add=False,download_images=True):
        self.update_description = update_description
        self.only_add = only_add
        self.download_images = download_images

    def get_brand_mapping(self, brand):
        log.info('Finding brand mapping for %s' % brand)
        try:
            self._brand_cache.setdefault(brand, BrandMapping.objects.using('default').get(
                brand=brand,
                account=self.config['ACCOUNT']))
            return self._brand_cache[brand]
        except BrandMapping.DoesNotExist:
            mapping = feedutils.get_or_create_brand_mapping(
                    account=self.config['ACCOUNT'],
                    ours = brand,
                    theirs = brand)
            self._brand_cache[brand] = mapping
            return mapping

    _category_cache = {}
    def get_category_mapping(self, category):
        log.info('Finding category mapping for %s' % category)
        try:
            self._category_cache.setdefault(category, CategoryMapping.objects.using('default').get(
                category=category,
                account=self.config['ACCOUNT']))
            return self._category_cache[category]
        except CategoryMapping.DoesNotExist:
            mapping = feedutils.get_or_create_category_mapping(
                    account=self.config['ACCOUNT'],
                    ours = category,
                    theirs = category)
            self._category_cache[category] = mapping
            return mapping

    _brand_blacklist_cache = {}
    def is_blacklisted_brand(self, brand):
        if brand in self._brand_blacklist_cache:
            return self._brand_blacklist_cache[brand]
        try:
            x = BrandBlackList.objects.using('default').get(account=self.config['ACCOUNT'],
                    brand=brand)
            self._brand_blacklist_cache[brand] = True
            return True
        except BrandBlackList.DoesNotExist:
            self._brand_blacklist_cache[brand] = False
            return False

    _category_blacklist_cache = {}
    def is_blacklisted_category(self, category):
        if category in self._category_blacklist_cache:
            return self._category_blacklist_cache[category]
        try:
            x = CategoryBlackList.objects.using('default').get(account=self.config['ACCOUNT'],
                    category=category)
            self._category_blacklist_cache[category] = True
            return True
        except CategoryBlackList.DoesNotExist:
            self._category_blacklist_cache[category] = False
            return False

    _sku_blacklist_cache = {}
    def is_blacklisted_sku(self, SKU):
        if SKU in self._sku_blacklist_cache:
            return self._sku_blacklist_cache[SKU]
        try:
            x = SKUBlackList.objects.using('default').get(account=self.config['ACCOUNT'],
                    sku=SKU)
            self._sku_blacklist_cache[SKU] = True
            return True
        except SKUBlackList.DoesNotExist:
            self._sku_blacklist_cache[SKU] = False
            return False

    _account = None
    def get_account(self):
        if not self._account:
            self._account = Account.objects.using('default').get(
                    code=self.config['ACCOUNT'])
        return self._account

    def _init_sync(self):
        ''' create a sync event to store the info about this sync '''
        sync = SyncEvent()
        sync.started_at = datetime.now()
        sync.account = self.config['ACCOUNT']
        sync.save(using='default')
        return sync

    def _end_sync(self, sync):
        ''' save the end of sync '''
        sync.ended_at = datetime.now()
        sync.status = 'finished'
        sync.save(using='default')
        return sync

    def get_matches(self, data):
        rate_chart, product = None, None
        try:
            rate_chart = SellerRateChart.objects.using('default').select_related('product').get(
                    sku = data['cleaned_data']['sku'],
                    seller = self.get_account())
            product = rate_chart.product
        except SellerRateChart.DoesNotExist:
            pass
            # TODO over optimization to avoid extra products. disabling for now

            #products = Product.objects.using('default').filter(
            #        brand=data['cleaned_data']['brand'],
            #        category=data['cleaned_data']['category'],
            #        model=data['cleaned_data']['model'])
            #if products:
            #    for p in products:
            #        if not p.sellerratechart_set.all():
            #            product = p
            #            break

        return (product, rate_chart)

    def get_or_create_feature_mapping(self, feature, product_type, feature_name):
        try:
            fm = FeatureMapping.objects.using('default').get(
                    feature = feature,
                    sku_type=product_type,
                    feature_name=feature_name,
                    account = self.config['ACCOUNT'],
                    )
        except FeatureMapping.DoesNotExist:
            fm = FeatureMapping(
                    feature = feature,
                    sku_type = product_type,
                    feature_name = feature_name,
                    account = self.config['ACCOUNT'],
                    data = ''
                    )
            fm.save(using='default')
        return fm


    _sku_type_map = {}
    def get_mapped_sku_type(self, sku_type):
        try:
            if str(sku_type) in self._sku_type_map:
                return self._sku_type_map.get(str(sku_type))
            mapping = SkuTypeProductTypeMapping.objects.using('default').get(
                    account = self.config['ACCOUNT'],
                    sku_type = sku_type)
            self._sku_type_map[str(sku_type)] = mapping.product_type
            return mapping.product_type
        except SkuTypeProductTypeMapping.DoesNotExist:
            return None

    def save_product_features(self, master, features, sku_type):
        if not features:
            return

        product_type = self.get_mapped_sku_type(sku_type)
        if not product_type:
            return

        for f in features:
            if type(features[f]).__name__ != 'list':
                if not features[f]:
                    continue
                if features[f] and not 'data' in features[f]:
                    continue
                if features[f]['data'] and features[f]['data'] != 'null':
                    try:
                        fm = FeatureMapping.objects.using('default').get(account = self.config['ACCOUNT'], sku_type = product_type, feature_name = f)
                        feature = fm.feature
                    except FeatureMapping.DoesNotExist:
                        try:
                            # See if a feature is already added to the system with given name for the same product type
                            feature = Feature.objects.using('default').get(product_type = product_type, name=f)
                            # If yes, then save this as mapping
                            fm = self.get_or_create_feature_mapping(feature, product_type, f)
                        except Feature.DoesNotExist:
                            feature = Feature(product_type = product_type, name=f)
                            if features[f]['type'] == 'char':
                                t = 'text'
                            if features[f]['type'] == 'int':
                                t = 'number'
                            else:
                                t = 'text'
                            feature.type = t
                            feature.save(using='default')
                            self.get_or_create_feature_mapping(feature, product_type, f)

                    try:
                        product_feature = ProductFeatures.objects.using('default').get(product=master,feature=feature)
                    except ProductFeatures.DoesNotExist:
                        product_feature = ProductFeatures(feature=feature,product=master)
                    try:
                        product_feature.data = self.clean_data((features[f]['data']))
                        product_feature.type = features[f].get('feature_type','fixed')
                        if master.type == 'variable':
                            if product_feature.type == 'variable':
                                product_feature.save(using='default')
                        else:
                            product_feature.save(using='default')
                    except Exception, e:
                        log.exception('Error saving feature %s for %s' % (feature.name, master.id))


    def clean_data(self,string):
        keys = [u'\xef',u'\xa0',u'\xa1',u'\xa2',u'\xa3',u'\xa4',u'\xa5',u'\xa6',u'\xa7',u'\xa8',u'\xa9',u'\xaa',u'\xab',u'\xac',u'\xad',u'\xae',u'\xaf',u'\xb0',u'\xb1',u'\xb2',u'\xb3',u'\xb4',u'\xb5',u'\xb6',u'\xb7',u'\xb8',u'\xb9',u'\xba',u'\xbb',u'\xbc',u'\xbd',u'\xbe',u'\xbf',u'\xef',u'\xeb',u'\xf6',u'\xd7',u'\x96',u'\x92']
        uni_str = unicode(string)
        for key in keys:
            uni_str = uni_str.replace(key,u'')

        if not uni_str:
            return ''
        string = uni_str.encode('utf-8')
        string = string.strip()
        return string.replace('\\t','')

    def update_master(self, product, data, sync):
        return self.create_master_product(data, sync, product, True)

    def create_master_product(self, data, sync, product=None, is_update=False):
        if not product:
            product = Product()
        product.title = data['cleaned_data']['title']
        product.description = data['cleaned_data']['detailed_desc'] or data['cleaned_data']['description']
        product.brand = data['cleaned_data']['brand']
        product.category = data['cleaned_data']['category']
        product.slug = slugify(product.title)[:150]
        product.model = data['cleaned_data']['model']
        product.moderate = True
        product.currency = data['cleaned_data'].get('currency','inr')
        product.type = data['cleaned_data'].get('product_type','normal')
        product.product_type = self.get_mapped_sku_type(data['cleaned_data'].get('sku_type',''))
        if data['cleaned_data'].get('video',''):
            product.video_embed = data['cleaned_data']['video']

        #If the category belongs to BLACKLIST_CATEGORIES, then set product.status = 'deactive'
        #else product.status = data['cleaned_data']['status']
        category = data['cleaned_data']['category']
        if str(category.ext_id) in getattr(settings, 'BLACKLIST_CATEGORIES', []):
            product.status = 'deactive'
        elif data['cleaned_data']['status'] in ['active','deactive','deleted']:
            product.status = data['cleaned_data']['status']

        product.save(using='default')
        product.productimage_set.using('default').all().delete()

        if self.download_images:
            # download the image
            for url in data['cleaned_data']['image_url']:
                try:
                    feedutils.attach_image_to_product(product,url)
                except Exception, e:
                    log.exception(
                            'Error adding image to product %s from %s: %s' % (
                                product.id, data['cleaned_data']['image_url'],
                                repr(e)))
        else:
            # Dont download images, we will serve them using their original urls
            for url in data['cleaned_data']['image_url']:
                pi = ProductImage(product=product, type='external')
                if 'scene7' in url:
                    pi.type = 'scene7'
                pi.name = product.title[:25]
                pi.url = url
                pi.save(using='default')

        if sync and not is_update:
            sync.new_masters += 1
            sync.save(using='default')
            #sync_product = SyncEventProductMapping(sync_event=sync,
            #        product=product, action='added')
            #sync_product.sku = data['cleaned_data']['sku']
            #sync_product.save(using='default')

        if sync and is_update:
            sync.edits += 1
            sync.save(using='default')
            #sync_product = SyncEventProductMapping(sync_event=sync,
            #        product=product, action='edited')
            #sync_product.sku = data['cleaned_data']['sku']
            #sync_product.save(using='default')

        return product

    def compute_transfer_price(self, data):
        # TODO we have to compute it from account data
        return None

    RC_DEFAULTS = {
            'sku':'',
            'is_prefered':True,
            'offer_price':Decimal('0'),
            'list_price':Decimal('0'),
            'transfer_price':Decimal('0'),
            'gift_title':'',
            'gift_desc':'',
            'warranty': '',
            #'status':'active',
            #'stock_status':'instock',
            'shipping_duration':'',
            'shipping_charges':Decimal('0'),
            'cod_charge':Decimal('0'),
            'payment_collection_charges':Decimal('0'),
            #'visibility_status':'always_visible',
            'shipping_paid_by':'vendor',
            'payment_charges_paid_by':'chaupaati',
            'otc':False,
            'ship_local_only':False,
            }
    def get_default_cleaned_data(self):
        return copy.deepcopy(self.RC_DEFAULTS)

    def get_rc_changes(self, rc, data):
        changes = {}
        cleaned_data = data['cleaned_data']

        fields = self.RC_DEFAULTS.keys()
        for field in fields:
            if getattr(rc, field) != cleaned_data[field]:
                changes[field] = dict(old=str(getattr(rc,field)),new=str(cleaned_data[field]))

        if cleaned_data['availability'].id != rc.availability_id:
            changes['availability_id'] = dict(old=rc.availability_id,
                    new=cleaned_data['availability'].id)

        return changes

    def create_update_seller_rate_chart(self, master, data, rc=None, sync=None):
        cleaned_data = data['cleaned_data']

        changes = {}
        action = 'edited'
        if not rc:
            rc = SellerRateChart()
            action = 'added'
        else:
            changes = self.get_rc_changes(rc, data)

        rc.product = master
        rc.sku = cleaned_data['sku']
        if 'external_product_id' in cleaned_data:
            rc.external_product_id = cleaned_data['external_product_id']
        if 'external_product_link' in cleaned_data:
            rc.external_product_link = cleaned_data['external_product_link']
        rc.seller = self.get_account()
        rc.is_prefered = cleaned_data['is_prefered']

        # prices
        rc.offer_price = cleaned_data['offer_price']
        rc.list_price = cleaned_data['list_price']
        rc.transfer_price = cleaned_data['transfer_price']
        rc.warranty = cleaned_data['warranty']
        rc.gift_desc = cleaned_data['gift_desc']
        rc.gift_title = cleaned_data['gift_title']
        rc.shipping_charges = cleaned_data['shipping_charges']
        rc.shipping_duration = cleaned_data['shipping_duration']
        if 'stock_status' in cleaned_data:
            rc.stock_status = cleaned_data['stock_status']

        rc.cod_charge = cleaned_data['cod_charge']
        rc.payment_collection_charges = cleaned_data['payment_collection_charges']
        #rc.visibility_status = cleaned_data['visibility_status']
        rc.shipping_paid_by = cleaned_data['shipping_paid_by']
        rc.payment_charges_paid_by = cleaned_data['payment_charges_paid_by']
        if 'status' in cleaned_data and cleaned_data['status'] in ['active','deactive']:
            rc.status = cleaned_data['status']
        rc.availability = cleaned_data['availability']
        if 'min_qty' in cleaned_data:
            rc.min_qty = cleaned_data['min_qty']

        rc.short_desc = cleaned_data.get('short_desc','')
        rc.detailed_desc = cleaned_data.get('detailed_desc','')
        rc.key_feature = cleaned_data.get('key_feature','')
        rc.article_id = cleaned_data.get('article_id','')
        rc.is_cod_available = cleaned_data.get('is_cod_available',False)
        rc.is_fmemi_available = cleaned_data.get('is_fmemi_available',False)
        rc.whats_in_the_box = cleaned_data.get('in_the_box','')
        rc.ship_local_only = cleaned_data.get('ship_local_only','')
        rc.otc = cleaned_data.get('otc','')
        #Populating shipping related info in SellerRateChart
        #rc.is_free_shipping = cleaned_data.get('is_free_shipping',False)
        #if not rc.is_free_shipping:
        #    rc.shipping_percent = cleaned_data.get('percent',Decimal("0.0"))
        #    rc.min_shipping = cleaned_data.get('min_shipping',Decimal("0.0"))
        #    rc.max_shipping = cleaned_data.get('max_shipping',Decimal("0.0"))
        rc.save(using='default')

        if sync:
        #    sync_rc_mapping = SyncEventRateChartMapping(sync_event=sync,
        #            rate_chart=rc, action=action)
        #    sync_rc_mapping.item_title = cleaned_data['title']
        #    sync_rc_mapping.sku = cleaned_data['sku']
            
            # nothing to save its not a real edit
            if action == 'edited' and changes:
                sync.edits += 1
                #sync_rc_mapping.change_log = simplejson.dumps(changes)
                #sync_rc_mapping.save(using='default')
                sync.save(using='default')
            if action == 'added':
                sync.adds += 1
                #sync_rc_mapping.save(using='default')
                sync.save(using='default')

        reindex = False
        if action == 'added' or changes:
            reindex = True

        return rc, reindex

    def delete_rate_chart(self, rc, sync):
        log.info("Deleting %s %s" % (rc.id, rc.sku))
        rc.stock_status = 'notavailable'
        rc.save(using='default')

        #sync_rc_mapping = SyncEventRateChartMapping(sync_event=sync,
        #        rate_chart=rc, action='marked_as_notavailable')
        #sync_rc_mapping.save(using='default')

        sync.deletes += 1
        sync.save(using='default')

    def delete_master_product(self, product, sync):
        product.status = 'deleted'
        product.save(using='default')

        #sync_product = SyncEventProductMapping(sync_event=sync, product=product,
        #        action='marked_as_deleted')
        #sync_product.save(using='default')

        sync.unavailable += 1
        sync.save(using='default')

    def post_process(self, info):
        ''' Here we apply the knowledge for this feed and modify cleaned data
        '''
        cleaned_data = info['cleaned_data']
        # knowledge can be fetched based on sku, brand, category
        pass

    def create_or_update_feature(self, product, mapping, data):
        feature = mapping.feature
        try:
            pf = ProductFeatures.objects.using('default').get(product=product, feature = feature)
        except ProductFeatures.DoesNotExist:
            pf = ProductFeatures(product = product, feature = feature)

        pf.data = data

        pf.clean()
        pf.save(using='default')

    def save_features(self, product, sku_type, features):
        # Features will be supplied as a map. We get the mapped feature
        # in our system using feature name and sku type
        try:
            for feature_name, data in features.iteritems():
                mapping = FeatureMapping.objects.using('default').get(sku_type = sku_type,
                        feature_name = feature_name)
                create_or_update_feature(product, mapping, data) 
        except Exception, e:
            log.exception('Error adding feature %s' % repr(e))

    def create_update_product_tags(self, product, tags):
        for tag_info in tags:
            tag_field = slugify(tag_info['value'])
            display_name = tag_info['value']
            tag_type = tag_info['type']
            try:
                tag = Tag.objects.using('default').get(tag = tag_field)
            except Tag.DoesNotExist:
                tag = Tag(display_name = display_name)
                tag.tag = tag_field
                tag.save(using='default')
            try:
                product_tag = ProductTags.objects.using('default').get(product = product, tag = tag, type = tag_type)
            except ProductTags.DoesNotExist:
                product_tag = ProductTags(product = product, tag = tag, type = tag_type)
                product_tag.save(using='default')

    def sync(self, *args, **kwargs):
        # Syncing catalog is split into
        # 01. Parsing the feed and obtaining a list of products as dictionaries
        # 02. Create masters and seller ratecharts or update seller rate charts
        # 03. Marking seller rate charts which were not present in the new feed as 
        #     deleted, mark affetcted products as unavailable
        try:
            sync = self._init_sync()
            # Step 01
            parsed_products = self.parse(sync, **kwargs)
            sync.found = len(parsed_products)
            sync.save(using='default')
            extra = 0
            # Step 02
            for info in parsed_products:

                has_variants = False
                if type(info) == list:
                    # product has variants
                    has_variants = True
                    to_add = info
                    extra += len(info)
                else:
                    to_add = [info]

                blueprint = None

                if has_variants:
                    # Lets try to get a blueprint which was already added for this group
                    for sku_info in to_add:
                        try:
                            rate_chart = SellerRateChart.objects.using('default').get(sku=sku_info['cleaned_data']['sku'], seller = self.get_account())
                            pv = ProductVariant.objects.using('default').filter(variant = rate_chart.product).order_by('id')
                            if pv:
                                blueprint = Product.objects.using('default').get(pk=pv[0].blueprint_id)
                        except Exception, e:
                            log.exception('Error finding blueprint for %s %s' % (sku_info['cleaned_data']['sku'], repr(e)))

                log.info(", ".join([pi['cleaned_data']['sku'] for pi in to_add]))
                for product_info in to_add:
                    db.reset_queries()
                    self.post_process(product_info)
                    master, rc = self.get_matches(product_info)

                    if master:
                        # found a master. this should be a variant
                        log.info('Found master %s' % master.id)
                        if master.type == 'normal' and has_variants:
                            # this was previously synced as a normal product
                            # we should now make this a variant
                            # update should take of this as product type is set
                            self.update_master(master, product_info, sync)

                            log.info('Updated master %s as %s' % (master.id, master.type))
                            if not blueprint:
                                # we do not have a blueprint, and have a new variant
                                # we will create a blueprint of this varaint
                                blueprint = master.create_as_blueprint()
                            pv = ProductVariant(
                                    blueprint=blueprint,
                                    variant=master,
                                    is_default_product=product_info['cleaned_data']['is_default_product'])
                            pv.save(using='default')
                            log.info('Added variant rel %s as %s of %s' % (master.id, master.type, blueprint.id))
                        else:
                            log.info('Updated master %s as %s' % (master.id, master.type))
                            self.update_master(master, product_info, sync)
                        # Add product tags
                        if product_info['cleaned_data'].get('tags',[]):
                            self.create_update_product_tags(master, product_info['cleaned_data']['tags'])

                    if not rc:
                        # no rate chart found. we might or might not have
                        # found a master. we used to guess a master before
                        # but now, we dont get a master if there is no rc
                        if not master:
                            # without a master, we have to create one
                            master = self.create_master_product(product_info, sync)
                            log.info('Created new master %s as %s' % (master.id, master.type))
                            if has_variants:
                                if not blueprint:
                                    # we do not have a blueprint, and have a new variant
                                    # we will create a blueprint of this varaint
                                    blueprint = master.create_as_blueprint()
                                pv = ProductVariant(
                                        blueprint=blueprint,
                                        variant=master,
                                        is_default_product=product_info['cleaned_data']['is_default_product'])
                                pv.save(using='default')
                                log.info('Added variant rel %s as %s of %s' % (master.id, master.type, blueprint.id))

                        elif master:
                            log.info('Updated master %s as %s' % (master.id, master.type))
                            self.update_master(master, product_info, sync)
                    if 'features' in product_info['cleaned_data']:
                        self.save_product_features(master,
                                product_info['cleaned_data']['features'],
                                product_info['cleaned_data'].get('sku_type', '--'))
                        if master.type == 'variant':
                            pv = ProductVariant.objects.using('default').filter(variant = master)
                            if pv:
                                pv = pv[0]
                                bluep = Product.objects.using('default').get(pk=pv.blueprint_id)
                                self.save_product_features(bluep,
                                    product_info['cleaned_data']['features'],
                                    product_info['cleaned_data'].get('sku_type', '--'))
                    rc, reindex = self.create_update_seller_rate_chart(master, product_info, rc, sync)

                    #Syncing bundle products
                    if 'bundle_skus' in product_info['cleaned_data']:
                        bundle_skus = product_info['cleaned_data']['bundle_skus']
                        if bundle_skus:
                            #Set is_bundle flag.
                            rc.is_bundle = True

                            for item in bundle_skus:
                                try:
                                    child_rc = SellerRateChart.objects.get(seller=rc.seller, sku=item)
                                    try:
                                        bundle_product = BundleProducts.objects.get(
                                            rate_chart = rc,
                                            bundle_src = child_rc)
                                    except BundleProducts.DoesNotExist:
                                        bundle_product = BundleProducts.objects.create(
                                            rate_chart = rc,
                                            bundle_src = child_rc)
                                except SellerRateChart.DoesNotExist:
                                    #If src does not exist for any of child src, delete all the 
                                    #bundle product objects created for this src so far.
                                    bundle_product = BundleProducts.objects.filter(
                                        rate_chart = rc)
                                    bundle_product.delete()
                                    break

                            #Recompute stock status.
                            if rc.bundle_products.all():
                                if rc.stock_status != 'instock' and rc.is_available_for_sale(None):
                                    rc.stock_status = 'instock'
                                    rc.save(using='default')
                                elif rc.stock_status == 'instock' and not rc.is_available_for_sale(None):
                                    rc.stock_status = 'outofstock'
                                    rc.save(using='default')
                            else:
                                rc.stock_status = 'notavailable'
                                rc.save(using='default')
                    
                    if 'fb_timed_price_lists' in product_info['cleaned_data']:
                        applicable_price_lists = product_info['cleaned_data']['fb_timed_price_lists']
                        timed_price_lists = product_info['cleaned_data']['fb_timed_price_lists']
                        if timed_price_lists:
                            for pricelist in timed_price_lists:
                                try:
                                    price = Price.objects.using('default').get(
                                        price_list = pricelist['price_list'], 
                                        rate_chart = rc, 
                                        price_type = 'timed',
                                        start_time = datetime.strptime(pricelist['start_time'],'%Y %m %d %H %M %S'),
                                        end_time = datetime.strptime(pricelist['end_time'],'%Y %m %d %H %M %S')
                                        )
                                except Price.DoesNotExist:
                                    price = Price(
                                        price_list=pricelist['price_list'], 
                                        rate_chart=rc, 
                                        price_type='timed', 
                                        start_time = datetime.strptime(pricelist['start_time'],'%Y %m %d %H %M %S'),
                                        end_time = datetime.strptime(pricelist['end_time'],'%Y %m %d %H %M %S')
                                       )

                                price.offer_price = pricelist['slot_price']
                                price.save(using='default')

                    if 'price_lists' in product_info['cleaned_data']:
                        applicable_price_lists = product_info['cleaned_data']['applicable_price_lists']
                        price_lists = product_info['cleaned_data']['price_lists']
                        if price_lists:
                            for pricelist in price_lists:
                                try:
                                    price = Price.objects.using('default').get(price_list=pricelist['price_list'], rate_chart=rc)
                                except Price.DoesNotExist:
                                    price = Price(price_list=pricelist['price_list'], rate_chart=rc)
                                except Price.MultipleObjectsReturned:
                                    price = Price.objects.using('default').filter(
                                        price_list=pricelist['price_list'], 
                                        rate_chart=rc,
                                        price_type='timed').exclude(
                                        Q(price_type='timed',start_time__gte=datetime.now())| 
                                        Q(price_type='timed', end_time__lte=datetime.now()))
                                    price = price[0]

                                price.list_price = pricelist['list_price']
                                price.offer_price = pricelist['offer_price']
                                price.save(using='default')

                                try:
                                    extprice = ExtPricelist.objects.using('default').get(rate_chart=rc,
                                        priceList=pricelist['price_list'], 
                                        account=Account.objects.using('default').get(code=self.config['ACCOUNT']))
                                except ExtPricelist.DoesNotExist:
                                    extprice = ExtPricelist(rate_chart=rc,
                                        priceList=pricelist['price_list'],
                                        account=Account.objects.using('default').get(code=self.config['ACCOUNT']))
                                extprice.list_price = pricelist['list_price']
                                extprice.offer_price = pricelist['offer_price']
                                extprice.save(using='default')
                            
                            #Delete the Price objects.using('default') which were available in previous feed sync, but not in current feed sync
                            #1) First, get the price lists for which current feed sync contains the Prices.
                            current_price_lists = []
                            for pricelist in price_lists:
                                current_price_lists.append(pricelist['price_list'])

                            #Now, get the price lists for which there were values in last feed sync, but not in current feed sync.
                            remove_price_lists = set(applicable_price_lists) - set(current_price_lists)
                            #Delete from Price and ExtPricelist
                            if remove_price_lists:
                                delete_price = Price.objects.using('default').filter(price_list__in=remove_price_lists, rate_chart=rc)
                                delete_price.delete()

                                delete_ext_price = ExtPricelist.objects.using('default').filter(rate_chart=rc,
                                    priceList__in=remove_price_lists,
                                    account=Account.objects.using('default').get(code=self.config['ACCOUNT']))
                                delete_ext_price.delete()
                        else:
                            #Delete all the existing Price and ExtPricelist as current feed sync does not contain prices for current seller rate chart. 
                            delete_price = Price.objects.using('default').filter(price_list__in=applicable_price_lists, rate_chart=rc)
                            delete_price.delete()

                            delete_ext_price = ExtPricelist.objects.using('default').filter(rate_chart=rc,
                                priceList__in=applicable_price_lists,
                                account=Account.objects.using('default').get(code=self.config['ACCOUNT']))
                            delete_ext_price.delete()

                    # Delete links from previous sync
                    reindex = True
                    if reindex:
                        log.info('Reindexing %s' % master.id)
                        master.update_solr_index(False)
                        if master.type == 'variant':
                            try:
                                pv = ProductVariant.objects.using('default').filter(variant = master)
                                if pv:
                                    bp = Product.objects.using('default').get(pk=pv[0].blueprint_id)
                                    bp.update_solr_index(False)
                            except:
                                log.info('Unable to find blueprint to update index')
                if blueprint:
                    blueprint.update_solr_index(False)

            sync.found += extra
            sync.save(using='default')

            if not self.only_add:
                # Step 03
                account_skus = set([x.sku for x in SellerRateChart.objects.using('default').filter(
                        seller=self.get_account())])
                new_skus = [] 
                for p in parsed_products:
                    if type(p) == list:
                        for v in p:
                            new_skus.append(v['cleaned_data']['sku'])
                    else:
                        new_skus.append(p['cleaned_data']['sku'])
                skus_to_delete = account_skus - set(new_skus)
                for sku in skus_to_delete:
                    db.reset_queries() 
                    rate_chart = SellerRateChart.objects.using('default').select_related(
                            'product').filter(
                            seller = self.get_account(),
                            sku = sku)
                    for item in rate_chart:
                        needs_deletion = False
                        if item.product.status == 'active':
                            if item.stock_status == 'instock':
                                needs_deletion = True
                            if not needs_deletion:
                                continue
                        self.delete_rate_chart(item, sync)
                        remaining_children = SellerRateChart.objects.using('default').filter(
                                product=item.product,
                                stock_status = 'instock').count()
                        if not remaining_children:
                            self.delete_master_product(item.product, sync)
                        item.product.update_solr_index(False)
                        p = item.product
                        if p.type == 'variant':
                            pv_set = ProductVariant.objects.using('default').filter(variant=p)
                            for pv in pv_set:
                                pv.blueprint.update_solr_index(False)
            sync = self._end_sync(sync)
        except Exception, e:
            import traceback
            import sys
            exc_info = sys.exc_info()
            st = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
            sync.stack_trace =  st
            sync.status = 'dead'
            sync.save(using='default')
            try:
                ip_address = get_ip('eth0')
                subject = 'Feed sync failed for %s from IP - %s' % (self.config['ACCOUNT'], ip_address)
                print subject
                body = st
                msg = EmailMessage(subject, body,
                    "Future Bazaar Reports<lead@futurebazaar.com>",
                    ['hemanth.goteti@futuregroup.in','suhas.kajbaje@futuregroup.in','krishna.raghavan@futuregroup.in','fb-dev@futuregroup.in'])
                msg.send()
            except:
                pass
                    
            log.exception('Error syncing feed for %s: %s' % (self.config['ACCOUNT'], repr(e)))
