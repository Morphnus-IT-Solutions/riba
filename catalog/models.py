from django.db import models
from tinymce.models import HTMLField
from utils.fields import CommaSeparatedCharField
import logging
from imagekit.models import ImageModel
from categories.models import *
from django.conf import settings
from south.modelsinspector import add_introspection_rules
from storage import upload_storage
from datetime import datetime, timedelta
from decimal import Decimal
from pricing.models import *
from django.db.models import Q
from django.template.defaultfilters import striptags, slugify
from django.core.cache import cache
from django.contrib.auth.models import User
log = logging.getLogger('request')

add_introspection_rules([],["^tinymce\.models\.HTMLField"])
# Create your models here.
class Brand(models.Model):
    class Meta:
        ordering = ('name',)

    name = models.CharField(max_length=50,unique=True)
    image = models.ImageField(blank=True, null=True, upload_to='brand/%Y/%m', storage=upload_storage)
    tagline = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null = True) 
    slug = models.SlugField(max_length=50,unique=True)

    moderate = models.BooleanField(default=False)

    def url(self):
        return "%s/bd/%s/" %  (self.slug, self.id)

    def __unicode__(self):
        return self.name

class ProductManager(models.Manager):
    use_for_related_fields = True

    def get_from_cache(self, key):
        try:
            return cache.get(key)
        except:
            return None

    def set_in_cache(self, key, data, expire):
        try:
            cache.set(key, data, expire)
        except:
            return

    def get_product(self, id, request, no_cache=False):
        obj = None
        key = 'catalog:product:%s' % id
        if not no_cache:
            obj = self.get_from_cache(key)
        if obj:
            return obj
        obj = self.get_query_set().select_related(
                'category', 'brand').get(pk=id)
        obj.primary_rate_chart()
        obj.default_variant()
        obj.get_product_images()
        obj.similar_products(request)
        # Cache for 60 minutes
        self.set_in_cache(key, obj, 60*60)
        return obj

class Product(models.Model):
    title = models.CharField(max_length=500)
    description = HTMLField()
    currency = models.CharField(max_length=3,default='inr',choices=(
        ('inr','inr'),
        ('usd','usd')))
    brand =  models.ForeignKey(Brand)
    model = models.CharField(max_length=100,blank=True)
    category = models.ForeignKey('categories.Category',verbose_name='Category')
    timestamp = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=150)
    page_title = models.CharField(max_length=100, blank=True)
    meta_description = models.TextField(blank=True)
    view_count = models.IntegerField(default=0)
    cart_count = models.IntegerField(default=0)
    pending_order_count =  models.IntegerField(default=0)
    confirmed_order_count = models.IntegerField(default=0)
    type = models.CharField(max_length=10,default='normal',choices=(
        ('variant','Variant'),
        ('normal','Normal'),
        ('variable','Variable')))

    status = models.CharField(max_length=15, db_index=True,
            default='active', choices=(
                ('active', 'Active'),
                ('deactive', 'Deactive'),
                ('deleted', 'Deleted')))
    has_images = models.BooleanField(default=False)
    video_embed = models.TextField(blank=True)
    modified_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True, auto_now=False)
    moderate = models.BooleanField(default=False, db_index=True)
    ext_large_image_url =  models.URLField(blank=True)
    ext_medium_image_url = models.URLField(blank=True)
    ext_small_image_url = models.URLField(blank=True)
    product_type = models.ForeignKey('categories.ProductType', blank=True, null=True)

    objects = ProductManager()
    is_online = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        obj = super(Product, self).save(*args, **kwargs)
        if self.id:
            cache.delete('catalog:product:%s' % self.id)
        return obj

    def url(self):
        return "%s/pd/%s/" % (self.slug, self.id)
    
    def quick_look_url(self):
        return "%s/quick-look/%s/" % (self.slug, self.id)

    def __unicode__(self):
        return self.title

    _variant_cache = None
    def default_variant(self, no_cache=False):
        if no_cache:
            variants = self.variants.filter(is_default_product=True)
            if variants:
                return variants[0].variant

        if self._variant_cache == None:
            variants = self.variants.filter(is_default_product=True)
            if variants:
                self._variant_cache = variants[0].variant
        return self._variant_cache

    _images_cache = None
    def get_product_images(self):
        if self._images_cache == None:
            self._images_cache = ProductImage.objects.filter(
                product=self).order_by('id')
            if self.type == 'variable' and not self._images_cache:
                self._images_cache = ProductImage.objects.filter(
                product = self.default_variant()).order_by('id')
        if self._images_cache:
            pass # Force evaluate
        return self._images_cache
        
    _primary_rate_chart_cache = None
    def primary_rate_chart(self, use_master=False):
        ''' Returns primary rate chart for the product or None '''
        if self._primary_rate_chart_cache:
            return self._primary_rate_chart_cache

        if self.type == 'normal' or self.type == 'variant':
            if use_master:
                preferred = self.sellerratechart_set.using(
                    'default').select_related(
                    'seller',
                    'seller__client').filter(is_prefered=True)[:2]
            else:
                preferred = self.sellerratechart_set.select_related(
                    'seller',
                    'seller__client').filter(is_prefered=True)[:2]
            if preferred:
                self._primary_rate_chart_cache = preferred[0]
                return preferred[0]
        if self.type == 'variable':
            if use_master:
                default_variants = ProductVariant.objects.using('default').select_related(
                    'variant').filter(blueprint=self,
                        is_default_product=True)[:2]
            else:
                default_variants = ProductVariant.objects.select_related(
                    'variant').filter(blueprint=self,
                        is_default_product=True)[:2]
            if default_variants:
                rc = default_variants[0].variant.primary_rate_chart()
                self._primary_rate_chart_cache = rc
                return rc
        return None

    _similar_products_cache = None
    def similar_products(self, request):
        ''' Guess related products of this product by issuing 
            a more like this query to solr.
        '''
        if self._similar_products_cache:
            return self._similar_products_cache
        params = {}
        params['mlt'] = 'true'
        params['mlt.fl'] = 'brand,category'
        params['mlt.mindf'] = 1
        params['mlt.mintf'] = 1
        params['mlt.count'] = 8
        params['qt'] = '/mlt'
        params['fq'] = 'client_id:%s AND inStock:true AND status:active AND visibility_s:always_visible' % request.client.client.id
        rc = self.primary_rate_chart()
        price_info = rc.getPriceInfo(request)
        offer_price = price_info.get('offer_price', None)
        if offer_price:
            params['fq'] = '%s AND %s:[%s TO %s]' % (params['fq'],
                           'offerprice_%s' % request.client.id,
                           '%.2f' % (Decimal('0.75') * offer_price),
                           '%.2f' % (Decimal('1.25') * offer_price))

        query = 'id:%s AND type:normal' % self.id
        solr_result = solr_search(query, fields='id', highlight=None,
                score=False, sort=None, sort_order="asc", **params)
        from utils import utils
        if solr_result:
            similar_product_ids = [int(doc['id']) for doc in solr_result.results]
            if self.id in similar_product_ids:
                similar_product_ids.remove(self.id)
            similar_products = utils.create_context_for_search_results(
                similar_product_ids, request)
            if request.client.client.name =='Holii':
                similar_products = Product.objects.filter(id__in = similar_product_ids)
                if len(similar_products)>5:
                    self._similar_products_cache = similar_products[0:5]
                    return self._similar_products_cache
                else:
                    self._similar_products_cache = similar_products
                    return self._similar_products_cache
            else:
                self._similar_products_cache = similar_products
                return self._similar_products_cache
        else:
            return []

    def update_solr_index(self, commit=True):
        self.reset_default_variant()
        if not self.primary_rate_chart(True):
            solr_delete(self.id)
            return
        data = dict(title=self.title, model=self.model, brand=self.brand.name,
            brand_id = self.brand.id, type = self.type,
            currency = self.currency, id = self.id,sku=self.primary_rate_chart().sku)
        data['__commit__'] = commit
        # TODO Assuming categories wont change so fast. Not forcing read from master
        cat_parents = self.category.get_all_parents() 
        cat_parents = sorted(cat_parents, key=lambda cat:cat.id)
        if cat_parents:
            category = [x.name for x in cat_parents]
            category.append(self.category.name)
            category_id = [str(x.id) for x in cat_parents]
            category_id.append(str(self.category.id))
        else:
            category = [self.category.name]
            category_id = [str(self.category.id)]

        data.update({'category_id':category_id,'category':category})

        features = []
        p_features = self.productfeatures_set.using('default').select_related(
            'feature', 'feature__group').all()
        for pf in p_features:
            is_present = False
            key = pf.feature.solr_key()
            value = pf.to_python_value()
            if pf.feature.index_for_presence:
                is_present = True
                if str(value).lower().startswith('no'):
                    is_present = False
                if str(value).lower().startswith('false'):
                    is_present = False
                fg = pf.feature.group
                if is_present:
                    if data.get('%s_pr_l' % fg.id):
                        data.get('%s_pr_l' % fg.id).append(pf.feature.id)
                    else:
                        data['%s_pr_l' % fg.id] = [pf.feature.id]
            data.update({key:value})
            if pf.feature.type == 'boolean' and pf.bool:
                features.append(pf.feature.name)
                continue
            pfsc = pf.productfeatureselectedchoice_set.using('default').select_related('choice').all()
            if pfsc:
                for sc in pfsc:
                    features.append(sc.choice.name)
                continue
        data.update({'features':features})

        try:
            psrcs = self.sellerratechart_set.using('default').all()
            seller_ids = []
            for src in psrcs:
                seller_ids.append(src.seller.id)
            data.update({'seller_id':seller_ids})
        except SellerRateChart.DoesNotExist:
            pass
        try:
            tags = self.producttags_set.using('default').all()
            if tags:
                tags_list, tag_id_list = [], []
                for tag in tags:
                    if tag.tag:
                        tags_list.append(tag.tag.tag)
                        tag_id_list.append(tag.tag.id)
                data['tags'] = tags_list
                data['tag_id'] = tag_id_list
            else:
                data['tags'] = []
                data['tag_id'] = []
        except:
            pass

        try:

            src = self.primary_rate_chart()
            '''
            Setting the product status depending on -
            1) primary_rate_chart.pricing_maintained = 'yes'
            2) primary_rate_chart.stock_status = 'instock'
            3) product.status = 'active'
            If (1),(2) and (3) are satisfied, then set status='active'
            else status='deactive'.
            '''
            product_status = 'active' 
            seller_names_to_exclude = ('HomeTown',)
            if not src.seller.name in seller_names_to_exclude:
                if (src.pricing_maintained != 'yes') or (src.stock_status != 'instock') or (self.status != 'active'):
                    product_status = 'deactive'
                    if self.is_online:
                        self.is_online = False
                        self.save()

            if product_status == 'active' and not self.is_online:
                self.is_online = True
                self.save()
            elif product_status != 'active' and self.is_online:
                self.is_online = False
                self.save()

            price = src.offer_price
            inStock = True
            if src.stock_status != 'instock':
                inStock = False
            if src:
                sku = src.sku
            else:
                sku = None

            client_id = src.seller.client.id
            applicable_price_lists = []
            client_domains = src.seller.client.clientdomain_set.using('default').all()

            for domain in client_domains:
                price_info = src.get_price_for_domain(domain)
                data.update({'offerprice_%s' % domain.id:price_info['offer_price'], 
                            'listprice_%s' % domain.id:price_info['list_price'], 
                            'discount_%s' % domain.id:price_info['discount']})

            data.update({'price':price,'inStock':inStock,'sku':sku,'client_id':client_id, 'status':product_status})
            if src.key_feature:
                data.update({'key_features': striptags(src.key_feature)})
            # Getting visibility status of an SRC
            visibility = src.visibility_status
            # Indexing visibility into dynamic field *_s
            data.update({'visibility_s': visibility})

        except SellerRateChart.DoesNotExist:
            pass
        except SellerRateChart.MultipleObjectsReturned:
            log.info('Found multiple rate charts for product %s' % self.id)

        # Indexing created_on time into timestamp
        data.update({'timestamp':self.created_on})

        #Add number of products sold in last 7 days
        from orders.models import OrderCount
        data['order_count'] = 0
        try:
            order_count_obj = OrderCount.objects.get(product=self)
            data['order_count'] = "%.0f" % order_count_obj.order_count
        except OrderCount.DoesNotExist:
            pass
        add_data(data)

    def formatted_currency(self):
        if self.currency == 'inr': return 'Rs.'
        if self.currency == 'usd': return 'USD'

    def reset_default_variant(self):
        if self.type != 'variable':
            return

        variantlinks = self.variants.all()
        found_instock_variant = False
        variants_count = variantlinks.count()
        count = 0
        for variantlink in variantlinks:
            count += 1
            variant = variantlink.variant
            rc = variant.primary_rate_chart()

            if not rc:
                continue
            
            if found_instock_variant:
                # if we found one, unset default product flag
                variantlink.is_default_product = False
                variantlink.save()
                continue

            if rc.stock_status in ['outofstock','notavailable']:
                if variantlink.is_default_product:
                    # if is default product and outofstock
                    # unset default product flag
                    variantlink.is_default_product = False
                    variantlink.save()

            if rc.stock_status == 'instock':
                found_instock_variant = True
                variantlink.is_default_product = True
                variantlink.save()
                self.status = 'active'
                self.save()
            if count == variants_count and not found_instock_variant:
                # If all variants are sold out
                # then make last variant as is_default variant
                variantlink.is_default_product = True
                variantlink.save()

        if not found_instock_variant:
            self.status = 'deactive'
            self.save()

    def short_title(self):
        return self.title
    
    def share(self, profile):
        from notifications.productsharingnotification import ProductSharingNotification
        rate_chart = self.primary_rate_chart()
        productsharingnotification = ProductSharingNotification(rate_chart, profile)
        productsharingnotification.send()
    
    def thumbnail(self):
        images = self.productimage_set.all().order_by('id')
        if images:
            thumbnail = images[0].thumbnail_image.name
        else:
            thumbnail = None
        return thumbnail

    def top10_url(self):
        images = self.productimage_set.all().order_by('id')
        if images:
            thumbnail = images[0].get_filmstrip_url()
        else:
            thumbnail = ''
        return thumbnail

    def get_large_thumb_url(self):
        images = self.productimage_set.all().order_by('id')
        if self.type == 'variable' and not images:
            df = self.default_variant()
            if df:
                images = df.productimage_set.all().order_by('id')
        if images:
            thumbnail = images[0].get_large_thumb_url()
        else:
            thumbnail = ''
        return thumbnail
    
    def battle_image_url(self):
        images = self.productimage_set.all().order_by('id')
        if self.type == 'variable' and not images:
            df = self.default_variant()
            if df:
                images = df.productimage_set.all().order_by('id')
        if images:
            thumbnail = images[0].get_battle_thumb_url(width=208,height=208)
        else:
            thumbnail = ''
        return thumbnail
        

    def search_image(self):
        images = self.productimage_set.all().order_by('id')
        if images:
            thumbnail = images[0].get_thumbnail_url()
        else:
            thumbnail = ''
        return thumbnail

    def category_thumbnail(self):
        images = self.productimage_set.all().order_by('id')
        if images:
            thumbnail = images[0].category_thumbnail.name
        else:
            thumbnail = None
        return thumbnail

    def get_thumbnail_150x150(self):
        images = self.productimage_set.all().order_by('id')
        if images:
            thumbnail = images[0].get_thumbnail_150x150()
        else:
            thumbnail = ''
        return thumbnail

    def get_thumbnail_60x60(self):
        images = self.productimage_set.all().order_by('id')
        if images:
            thumbnail = images[0].get_thumbnail_60x60()
        else:
            thumbnail = ''
        return thumbnail

    def get_display_300x300(self):
        images = self.productimage_set.all().order_by('id')
        if images:
            thumbnail = images[0].get_display_300x300()
        else:
            thumbnail = ''
        return thumbnail

    def create_as_blueprint(self):
        cloned = Product()
        simple_clones = ['title','description','currency','model','slug','page_title']
        simple_clones += ['meta_description','status','type','video_embed']
        for key in simple_clones:
            setattr(cloned, key, getattr(self, key))
        cloned.type = 'variable'
        cloned.brand = self.brand
        cloned.category = self.category
        cloned.save()
        return cloned

        # TODO clone product images
        # TODO clone product features
        # TODO clone product tags
    _default_img_cache = None
    def get_default_img(self):
        images = self.productimage_set.all().order_by('id')[:1]
        if images:
            self._default_img_cache = images[0]
            return self._default_img_cache.get_filmstrip_url()
        return None

    def is_new_arrival(self):
        last_15_days = datetime.now() + timedelta(days=-15)
        if self.created_on >= last_15_days:
            return True 
        return False

class ProductImage(ImageModel):
    product = models.ForeignKey(Product)
    image = models.ImageField(upload_to='product/%Y/%m', storage=upload_storage,blank=True,null=True)
    name = models.CharField(max_length=25)
    url = models.URLField(blank = True, null = True, verify_exists=False)
    type = models.CharField(max_length=15,null =True, blank = True,default='local',choices=(
            ('local', 'Local'),
            ('scene7', 'Scene7')
            ))
    
    class IKOptions:
        # This inner class is where we define the ImageKit options for the model
        spec_module = 'catalog.specs'
        cache_dir = 'pc'
        image_field = 'image'

    def get_large_thumb_url(self,height=150, width = 150):
        if self.type == 'local':
            return self.display.url
        else:
            p1 = re.compile('wid=\d*')
            p2 = re.compile('hei=\d*')
            p3 = re.compile('M1')
            url = p1.sub('wid=%s' % width,self.url)
            url = p2.sub('hei=%s' % height,url)
            url = p3.sub('T1', url)
            p4 = re.compile('www.futurebazaar.com')
            url = p4.sub('fbcdn.mediafb.com', url)
            return url

    def get_battle_thumb_url(self,height=150, width = 150):
        if self.type == 'local':
            return self.display.url
        else:
            p1 = re.compile('wid=\d*')
            p2 = re.compile('hei=\d*')
            url = p1.sub('wid=%s' % width,self.url)
            url = p2.sub('hei=%s' % height,url)
            p4 = re.compile('www.futurebazaar.com')
            url = p4.sub('fbcdn.mediafb.com', url)
            return url

    def get_large_image_url(self, height = 600, width = 450):
        if self.type == 'local':
            return self.large_image.url
        else:
            p1 = re.compile('wid=\d*')
            p2 = re.compile('hei=\d*')
            url = p1.sub('wid=%s' % width,self.url)
            url = p2.sub('hei=%s' % height,url)
            p4 = re.compile('www.futurebazaar.com')
            url = p4.sub('fbcdn.mediafb.com', url)
            return url

    def get_zooming_image_url(self, height = 1000, width = 800):
        if self.type == 'local':
            return self.large_image.url
        else:
            p1 = re.compile('wid=\d*')
            p2 = re.compile('hei=\d*')
            url = p1.sub('wid=%s' % width,self.url)
            url = p2.sub('hei=%s' % height,url)
            p4 = re.compile('www.futurebazaar.com')
            p5 = re.compile('M1')
            url = p4.sub('fbcdn.mediafb.com', url)
            url = p5.sub('L1', url)
            return url
       
    def get_display_url(self,height=340,width = 270): 
        if self.type == 'local':
            return self.display.url
        else:
            p1 = re.compile('wid=\d*')
            p2 = re.compile('hei=\d*')
            url = p1.sub('wid=%s' % width,str(self.url))
            url = p2.sub('hei=%s' % height,url)
            p4 = re.compile('www.futurebazaar.com')
            url = p4.sub('fbcdn.mediafb.com', url)
            return url

    def get_filmstrip_url(self,height=48,width = 48): 
        if self.type == 'local':
            return self.filmstrip.url
        else:
            p1 = re.compile('wid=\d+')
            p2 = re.compile('hei=\d+')
            p3 = re.compile('M1')
            url = p1.sub('wid=%s' % width,self.url)
            url = p2.sub('hei=%s' % height,url)
            url = p3.sub('T1', url)
            p4 = re.compile('www.futurebazaar.com')
            url = p4.sub('fbcdn.mediafb.com', url)
            return url

    def get_thumbnail_url(self,height=150,width = 150): 
        if self.type == 'local':
            return self.thumbnail_image.url
        else:
            p1 = re.compile('wid=\d+')
            p2 = re.compile('hei=\d+')
            p3 = re.compile('M1')
            url = p1.sub('wid=%s' % width,self.url)
            url = p2.sub('hei=%s' % height,url)
            url = p3.sub('T1', url)
            p4 = re.compile('www.futurebazaar.com')
            url = p4.sub('fbcdn.mediafb.com', url)
            return url

    def get_display_350x350(self):
        return self.display_350x350.url

    def get_display_300x300(self):
        return self.display_300x300.url

    def get_thumbnail_150x150(self):
        return self.thumbnail_150x150.url

    def get_thumbnail_60x60(self):
        return self.thumbnail_60x60.url

class ProductFeatures(models.Model):
    class Meta:
        verbose_name_plural = 'Product Features'
    product = models.ForeignKey(Product)
    feature = models.ForeignKey('categories.Feature')
    data = models.CharField(max_length=1000)
    value = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True)
    bool = models.BooleanField(default=False)
    type = models.CharField(max_length=10,default='fixed',choices=(
        ('fixed','Fixed'),
        ('variable','Variable')))

    def to_python_value(self):
        from categories.models import FeatureChoice
        choices = FeatureChoice.objects.filter(feature=self.feature)
        if choices:
            selected_choices = [choice.choice.name for choice in 
                    ProductFeatureSelectedChoice.objects.filter(product_feature=self)]
            return selected_choices
            
        if self.feature.type == 'number':
            return self.value
        if self.feature.type == 'boolean':
            return self.bool
        if self.feature.type == 'text':
            return self.data

    def humanized_value(self):
        python_val = self.to_python_value()
        if type(python_val) == list:
            return ", ".join(python_val)
        if self.feature.type == 'number' and self.feature.unit:
            return '%s %s' % (python_val, self.feature.unit.code)
        return python_val
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.feature.category and self.product.category and self.feature.category.id != self.product.category.id:
            raise ValidationError('Product category and feature category should match')
        if self.feature.type == 'boolean':
            if self.data not in ['Yes','True','Y','y','yes','true','No','no','False','false']:
                raise ValidationError('Invalid value for boolean feature')
        if self.feature.type == 'number':
            try:
                f = float(self.data)
            except:
                raise ValidationError("Data should be number")
        from categories.models import FeatureChoice
        choices = FeatureChoice.objects.filter(feature=self.feature)
        if choices:
            input = [i.strip() for i in self.data.split(',')]
            if not self.feature.allow_multiple_select and len(input) > 1:
                raise ValidationError('Only one choice is allowed for %s' % self.feature.name)
            not_permitted = set(input) - set([choice.name for choice in choices])
            if not_permitted:
                raise ValidationError('%s is not a valid entry for %s' % 
                (", ".join(list(not_permitted)) ,self.feature.name))


    def __unicode__(self):
        return '%s-%s' % (self.feature.name, self.product.category)

    def save(self, *args, **kwargs):
        # set the corresponding keys based on type of data
        import decimal
        if self.feature.type == 'number':
            self.value = decimal.Decimal(str(float(self.data)))
            self.bool = False
        if self.feature.type == 'boolean':
            if self.data in ['Yes', 'True', 'yes','true','y','Y']:
                self.bool = True
            self.value = None
        # call parent save to do actual save
        super(ProductFeatures, self).save(*args, **kwargs)
        # update the selected choices
        choices = FeatureChoice.objects.filter(feature=self.feature)
        if choices:
            input = [i.strip() for i in self.data.split(',')]
            for choice in choices:
                # for all the allowed choices
                if choice.name in input:
                    # if the choice is selected
                    try:
                        existing = ProductFeatureSelectedChoice.objects.get(
                                product_feature=self, choice=choice)
                    except ProductFeatureSelectedChoice.DoesNotExist:
                        # and does not already exist in the db
                        pfsc = ProductFeatureSelectedChoice()
                        pfsc.choice = choice
                        pfsc.product_feature = self
                        # save it
                        pfsc.save()
                else:
                    # if exists but not selected, delete it
                    try:
                        existing = ProductFeatureSelectedChoice.objects.get(
                                product_feature=self, choice=choice).delete()
                    except ProductFeatureSelectedChoice.DoesNotExist:
                        pass
                        

class ProductFeatureSelectedChoice(models.Model):
    class Meta:
        unique_together = ('choice','product_feature')

    choice = models.ForeignKey('categories.FeatureChoice')
    product_feature = models.ForeignKey(ProductFeatures)

    def __unicode__(self):
        return self.choice.name

class Availability(models.Model):
    name = models.CharField(max_length=30)
    class Meta:
        verbose_name_plural = 'Availability info'

    def __unicode__(self):
        constraints = self.availabilityconstraint_set.all()
        return "\n".join([constr.__unicode__() for constr in constraints])

class AvailabilityConstraint(models.Model):
    availability  = models.ForeignKey(Availability)
    status = models.CharField(max_length=15,default='available',choices=(
        ('available','Available'),
        ('unavailable','Unavailable')))
    zone = models.CharField(max_length=10,default='country',choices=(
        ('country','Country'),
        ('state','State'),
        ('city','City'),
        ('zipcode','Zipcode')))
    zipcode = models.TextField(blank=True)
    country = models.ForeignKey('locations.Country',blank=True,null=True)
    city = models.ForeignKey('locations.City',blank=True,null=True)
    state = models.ForeignKey('locations.State',blank=True,null=True)

    def __unicode__(self):
        str = '%s in %s: ' % (self.get_status_display(), self.zone)
        if self.zone == 'zipcode':
            str += '%s' % self.zipcode
        if self.zone == 'state':
            str += '%s' % self.state
        if self.zone == 'country':
            str += '%s' % self.country
        if self.zone == 'city':
            str += '%s' % self.city
        return str

class SellerRateChartQuerySet(models.query.QuerySet):

    def get_from_cache(self, key):
        try:
            return cache.get(key)
        except:
            return None

    def set_in_cache(self, key, obj, expire):
        try:
            cache.set(key, obj, expire)
        except:
            pass

    def get(self, *args, **kwargs):
        if 'id' in kwargs and kwargs.keys() == ['id']:
            obj = self.get_from_cache('catalog:sellerratechart:%s' % kwargs['id'])
            if obj:
                return obj
            else:
                obj = super(SellerRateChartQuerySet, self).get(*args, **kwargs)
                obj.product
                self.set_in_cache('catalog:sellerratechart:%s' % obj.id, obj, 0)
                return obj

        if 'pk' in kwargs and kwargs.keys() == ['pk']:
            obj = self.get_from_cache('catalog:sellerratechart:%s' % kwargs['pk'])
            if obj:
                return obj
            else:
                obj = super(SellerRateChartQuerySet, self).get(*args, **kwargs)
                obj.product
                self.set_in_cache('catalog:sellerratechart:%s' % obj.id, obj, 0)
                return obj
        return super(SellerRateChartQuerySet, self).get(*args, **kwargs)


class SellerRateChartManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return SellerRateChartQuerySet(self.model)


class SellerRateChart(models.Model):
    product = models.ForeignKey(Product)
    sku = models.CharField(max_length=100, db_index=True)
    article_id = models.CharField(max_length=100, db_index=True, blank=True)
    short_desc = HTMLField(blank=True, null=True)
    key_feature = HTMLField(blank=True, null=True)
    detailed_desc = HTMLField(blank=True, null=True)
    external_product_id = models.CharField(max_length=100,blank=True)
    external_product_link = models.URLField(blank=True)
    seller = models.ForeignKey('accounts.Account',related_name='products_offered',verbose_name='Seller')
    condition = models.CharField(max_length=5,default='new',choices=(
        ('new','New'),
        ('used','Used')), db_index=True)
    is_prefered = models.BooleanField(default=False,
            help_text='Is this seller the preferred seller for this product on chaupaati')
    list_price = models.DecimalField(max_digits=10, decimal_places=2,
            null=True, verbose_name='List Price')
    transfer_price = models.DecimalField(max_digits=10, decimal_places=2,
            null=True, verbose_name='Transfer Price')
    offer_price = models.DecimalField(max_digits=10, decimal_places=2,
            null=True, verbose_name='Offer Price')
    cashback_amount = models.DecimalField(max_digits=10, decimal_places=2,
            null=True, verbose_name='Cashback', blank=True)
    warranty = models.CharField(max_length=100,blank=True)
    gift_title = models.CharField(max_length=500,blank=True)
    gift_desc = models.TextField(blank=True)
    shipping_charges = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    shipping_duration = models.CharField(max_length=50,blank=True)
    is_free_shipping = models.BooleanField(default=False)#Free shipping applicable or not
    shipping_percent = models.DecimalField(max_digits=4, decimal_places=2, null=True)#Shipping charge in percent
    min_shipping = models.DecimalField(max_digits=10, decimal_places=2, null=True) #Minimum shipping charges
    max_shipping = models.DecimalField(max_digits=10, decimal_places=2, null=True) #Maximum shipping charges
    #availability = models.ForeignKey(Availability, verbose_name='Ships to')
    stock_status = models.CharField(max_length=100,default='instock',choices=(
        ('instock','In Stock'),
        ('outofstock','Out of Stock'),
        ('notavailable','Not Available')))
    #Flag for checking whether valid prices and pricelist priorities are maintained or not.
    pricing_maintained = models.CharField(max_length=100,default='no',choices=(
        ('yes','Yes'),
        ('no','No')))
    min_qty = models.PositiveIntegerField(default=1)
    cod_charge = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    payment_collection_charges = models.BooleanField(default=False)
    visibility_status = models.CharField(max_length=100, default='always_visible', choices=(
        ('always_visible','Visible on CC and Web'),
        ('only_cc','Only CC'),
        ('only_web','Only Web'),
        ('only_godrej', 'Only Godrej')), db_index=True)
    shipping_paid_by = models.CharField(max_length=15, default='vendor', choices=(
        ('chaupaati','Chaupaati'),
        ('vendor','Vendor')))
    payment_charges_paid_by = models.CharField(max_length=15,
            default='chaupaati', choices=(
            ('chaupaati','Chaupaati'),
            ('vendor','Vendor'))
            )
    is_cod_available = models.BooleanField(default=False)
    is_fmemi_available = models.BooleanField(default=False)
    cod_available_at = models.ForeignKey(Availability, related_name='cod_available_at', blank=True,null=True)
    whats_in_the_box = models.TextField(blank=True)
    ship_local_only = models.BooleanField(default=False)
    home_deliverable = models.BooleanField(default=False)
    otc = models.BooleanField(default=False)
    is_so_available = models.BooleanField(default=False)
    is_bundle = models.BooleanField(default=False)

    objects = SellerRateChartManager()
    

    def save(self, *args, **kwargs):
        if self.id:
            cache.delete('catalog:sellerratechart:%s' % self.id)
        return super(SellerRateChart, self).save(*args, **kwargs)
    

    def clean(self):
        import decimal
        if self.list_price <= decimal.Decimal('0.00'):
            self.list_price = self.offer_price

    def __unicode__(self):
        return 'Rate chart for %s by %s' % (self.product.title, self.seller.name)

    def get_external_product_link(self):
        return self.external_product_link.replace(' ','%20')

    def getSavings(self):
        if self.list_price:
            return self.list_price - self.offer_price

    def getDiscount(self):
        if self.list_price:
            return int(round((Decimal(self.getSavings())/Decimal(self.list_price))*100))

    def getInventory(self):
        inv = self.inventory_set.all()
        inv = inv and inv[0].stock or Decimal(0)
        return inv

    def get_fb_stock_status(self):
        if self.stock_status == 'outofstock' or self.stock_status == 'notavailable':
            return 'outofstock'
        return 'instock'

    def get_availability_status(self):
        # This function returns the availability status
        # of a rate_chart obj, which can be
        # instock - physical inventory is available
        # backorder - physical inventory is not available but 
        #             virtual inventory is available
        # outofstock - physical and virtual inventories are not available
        current_time = datetime.now()
        shipping_time = None
        status_info = {}
        status_info['shipping_time'] = shipping_time
        if self.is_bundle:
            #Get all the children
            children = self.bundle_products.all()
            rate_charts = [child.bundle_src for child in children]
            inventory_statuses = []
            for rate_chart in rate_charts:
                inventory_status_info = rate_chart.get_availability_status()
                if inventory_status_info['status'] == 'outofstock':
                    return inventory_status_info
                else:
                    # set as {shipping_date:status}, then sort it
                    # by shipping_date desc
                    info = {inventory_status_info['shipping_time']:inventory_status_info['status']}
                    inventory_statuses.append(info)
            if inventory_statuses:
                for shipping_time, status in max(inventory_statuses).iteritems():
                    status_info['status'] = status
                    status_info['shipping_time'] = shipping_time
                    return status_info
            status_info['status'] = 'outofstock'
            return status_info
        else:
            # get all inventory levels (physical + VI)            
            all_inventory_levels = {}
            inventories = Inventory.objects.filter(
                rate_chart = self,
                is_active = True,
                starts_on__lte = current_time,
                ends_on__gte = current_time)
            for inventory in inventories:
                if inventory.type in all_inventory_levels:
                    all_inventory_levels[inventory.type].append(inventory)
                else:
                    all_inventory_levels[inventory.type] = [inventory]
            # first check for physical inventories,
            # if present then status instock    
            status = None
            physical_inventory_levels = []
            if 'physical' in all_inventory_levels:
                physical_inventory_levels = all_inventory_levels.pop('physical')
            for inventory in physical_inventory_levels:
                if inventory.compute_ats() > Decimal('0'):
                    # if instock then shipping date = 1 + datetime.now()
                    shipping_time = 1 
                    status = 'instock'
                    break
            if status == 'instock':
                status_info['status'] = 'instock'
                status_info['shipping_time'] = shipping_time
                return status_info
            # physical inventory not available
            # check for virtual inventory              
            inventory_statuses = []
            for status, inventories in all_inventory_levels.iteritems():
                shipping_time = 1
                status_time_map = {
                    'backorder':3,
                    'preorder':1,
                    'madetoorder':3,
                }
                if status in status_time_map:
                    shipping_time = status_time_map[status]
                    for inventory in inventories:                    
                        # for loop for multiple dcs 
                        if inventory.compute_ats() > Decimal('0'):
                            if status == 'preorder':
                                # if pre_order shipping date = expected_on + 1
                                if not inventory.expected_on:
                                    # invalid entry for pre order
                                    log.exception("Expected on not set for \
                                                 Preorder inventory, ID: %s" % inventory.id)
                                    continue
                                shipping_time = (inventory.expected_on.date() - current_time.date()).days\
                                                 + shipping_time
                            elif status == 'madetoorder':
                                # if made_to_order shipping date = expected_in + 3
                                if not inventory.expected_in:
                                    # invalid entry for madetoorder
                                    log.exception("Expected in not set for \
                                                Made To order inventory, ID: %s" % inventory.id)
                                    continue
                                shipping_time = shipping_time + inventory.expected_in
                            info = {shipping_time:status}
                            inventory_statuses.append(info)
                else:
                    # Should not enter in this section after dividing virtual entry into
                    #  - backorder
                    #  - madetoorder
                    #  - preorder
                    for inventory in inventories:                    
                        if inventory.compute_ats() > Decimal('0'):
                            if not inventory.expected_on and not inventory.expected_in:
                                # if backorder shipping date = 3 + datetime.now()
                                inventory_status = 'backorder'
                                shipping_time = status_time_map[inventory_status] 
                            elif inventory.expected_on:
                                # if pre_order shipping date = expected_on + 1
                                inventory_status = 'preorder'
                                shipping_time = (inventory.expected_on.date() - current_time.date()).days\
                                                 + status_time_map[inventory_status]
                            elif inventory.expected_in:
                                # if made_to_order shipping date = expected_in + 3
                                inventory_status = 'madetoorder'
                                shipping_time = status_time_map[inventory_status] + inventory.expected_in
                            else:
                                log.exception("Invalid Inventory maintained for: %s" % self)                    
                                continue
                            info = {shipping_time:inventory_status}
                            inventory_statuses.append(info)
            if inventory_statuses:
                for shipping_time, status in min(inventory_statuses).iteritems():
                    status_info['status'] = status
                    status_info['shipping_time'] = shipping_time
                    return status_info
        status_info['status'] = 'outofstock'
        return status_info 

    def get_from_cache(self, key):
        try:
            return cache.get(key)
        except:
            return None

    def set_in_cache(self, key, data, expire):
        try:
            cache.set(key, data, expire)
        except:
            return

    def get_price_for_domain(self, client_domain, prices=None, **kwargs):
        '''
            Calculate the offer price: 
                1) DomainLevelPriceList.order_by(priority)
                2) ClientLevelPriceList.order_by(priority)
                3) Offer price in SellerRateChart (Default Offer Price)
        '''
        dont_cache = kwargs.get('dont_cache', False)
        expires = 0
        from_cache = self.get_from_cache('catalog:src:%s:price:%s' % (self.id, client_domain.id)) 
        if from_cache and not dont_cache:
            return from_cache
        offer_price = self.offer_price
        list_price = self.list_price
        cashback_amount = self.cashback_amount
        payback_points = self.offer_price * 4
        offer_price_label = "Steal Price:"
        list_price_label = "Market Price:"
        cashback_amount_label = "Cashback"
        from utils import utils
        if utils.is_wholii_client(client_domain.client) or utils.is_usholii_client(client_domain.client):
            currency = 'usd'
        else:
            currency = "inr"
        now = datetime.now()
        applicable_price_lists = []
        applicable_price = None
        price_list = None
        discount = self.getDiscount()
        savings = self.getSavings()
        get_price_type = kwargs.get('price_type', None)
        # How to optimize this? Lets think
        # Get all the prices
        if not prices:
            prices = Price.objects.select_related('price_list').filter(
                rate_chart=self).exclude(
                Q(price_type='timed',start_time__gte=datetime.now())| 
                Q(price_type='timed', end_time__lte=datetime.now())
                )
            
            if get_price_type == 'next_price':
                time_delta = int(kwargs.get('time_delta', 2))                
                todays_price_datetime = datetime.now() + timedelta(hours=+time_delta)
                prices = Price.objects.select_related('price_list').filter(price_type='timed', rate_chart=self, 
                         start_time__lte=todays_price_datetime, end_time__gte=todays_price_datetime)
                if not prices:
                    todays_price_datetime = datetime.now() + timedelta(hours=-time_delta)
                    prices = Price.objects.select_related('price_list').filter(price_type='timed', rate_chart=self, 
                             start_time__lte=todays_price_datetime, end_time__gte=todays_price_datetime)

        # Now that we have all the prices, there are couple of things to do
        # - Exclude prices in pricelists which do not belong to this req
        #   We may even do this directly in the query
        # - Once we have final set, lets prioritize
        prices_map = dict([(price.price_list.id, price) for price in prices])


        #Get PriceList ordered by priority for current domain
        domain_level_pricelist = client_domain.get_price_lists()
        if domain_level_pricelist:
            for dlp in domain_level_pricelist:
                applicable_price_lists.append(dlp.price_list)
        
        #Get PriceList ordered by priority for current client
        client_level_pricelist = client_domain.client.get_price_lists()

        if client_level_pricelist:
            for clp in client_level_pricelist:
                applicable_price_lists.append(clp.price_list)
        #Now applicable_price_lists contains pricelists in the order. Iterate and see which is applicable.
        index = -1
        for apl in applicable_price_lists:
            index+=1
            applicable_prices = prices_map.get(apl.id, None)
            if applicable_prices:
                applicable_price = applicable_prices
                break
       
        if applicable_price:
            #Now get the populate the info depending on Price object
            list_price = applicable_price.list_price
            offer_price = applicable_price.offer_price
            cashback_amount = applicable_price.cashback_amount
            currency = applicable_price.price_list.currency
            list_price_label = applicable_price.price_list.list_price_label
            offer_price_label = applicable_price.price_list.offer_price_label
            if applicable_price.price_type == 'timed':
                td = applicable_price.end_time - datetime.now()
                if td > timedelta(seconds=0):
                    expires = td.seconds + 24*60*60*td.days
                    if expires > 24*60*60:
                        expires = 24*60*60

            #If applicable price does not contain list price, iterate through remaining applicable pricelist objects and get it
            if list_price == Decimal("0.00"):
                for apl in applicable_price_lists[index:]:
                    #applicable_prices = Price.objects.filter(price_list=apl, rate_chart=self).exclude(Q(price_type='timed',start_time__gte=datetime.now())| Q(price_type='timed', end_time__lte=datetime.now())).order_by('-price_type')
                    applicable_prices = prices_map.get(apl.id, None)
                    if applicable_prices:
                        if applicable_prices.list_price != Decimal("0.00"):
                            list_price = applicable_prices.list_price
                            break

            #If it still remains 0.00, assign default seller rate chart value.
            if not list_price:
                list_price = self.list_price
            
            if list_price and offer_price:
                savings = list_price - offer_price
                discount = int(round(((Decimal(list_price)-Decimal(offer_price))/Decimal(list_price))*100))
                
            if not savings:
                savings = Decimal('0')
            if not discount:
                discount = Decimal('0')

            if cashback_amount:
                payback_points = (offer_price-cashback_amount)*4
            else:
                payback_points = offer_price*4

        info = {'offer_price':offer_price,'list_price':list_price,'currency':currency,
                'offer_price_label':offer_price_label,'list_price_label':list_price_label,
                'price_list':price_list, 'discount':discount,'applicable_price':applicable_price,
                'savings':savings, 'payback_points':payback_points,
                'cashback_amount':0}#cashback_amount if cashback_amount else Decimal('0')}
        if not dont_cache:
            # Dont cache for more than 10 mins
            expires = 10*60
            self.set_in_cache('catalog:src:%s:price:%s' % (self.id, client_domain.id),
                info, expires)
        return info

    def getPriceInfo(self, request, prices=None, **kwargs):
        info = self.get_price_for_domain(request.client, prices, **kwargs)
        return info
    
    #Required Anubhav
    def getPriceByPriceList(self, request, price_list):
        price_list = price_list.get('price_list')
        if not (price_list):
            return self.getPriceInfo(request)
        info = {}
        try:
            price_list = PriceList.objects.get(name=price_list)
            price_info = Price.objects.get(rate_chart=self, price_list=price_list)
            info['list_price'] = price_info.list_price
            info['offer_price'] = price_info.offer_price
            info['cashback_amount'] = price_info.cashback_amount
        except:
            pass
        return info

class BundleProducts(models.Model):
    rate_chart = models.ForeignKey(SellerRateChart, related_name='bundle_products')
    bundle_src = models.ForeignKey(SellerRateChart, related_name='+')
    qty = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)


class ShippingInfo(models.Model):
    class Meta:
        verbose_name_plural = 'Product shipping metrics'
        verbose_name = 'Product shipping metric'
    product = models.ForeignKey(Product)
    weight = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    length = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    bredth = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    height = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    

class ProductVariant(models.Model):
    blueprint = models.ForeignKey(Product,related_name='variants',limit_choices_to=dict(type='variable'))
    variant = models.ForeignKey(Product,limit_choices_to=dict(type='variant'))
    is_default_product = models.BooleanField()

class Tag(models.Model):
    tag = models.CharField(max_length=100,blank=False)
    display_name = models.CharField(max_length=100)
    type = models.CharField(max_length=25, default='', blank=True, null=True, choices=(
        ('clearance', 'Clearance'),
        ('retailers', 'Retailers'),
        ('visibility', 'Visibility'),
    ))
    
    def __unicode__(self):
        return self.display_name

class ProductTags(models.Model):
    class Meta:
        unique_together = ('tag', 'product', 'type')

    product = models.ForeignKey(Product)
    tag = models.ForeignKey(Tag,blank=True,null=True)
    type = models.CharField(max_length=25,default='facet',choices=(
        ('battle','Battle'),
        ('friday_deal','Friday Deal'),
        ('clearance_sale','Clearance Sale'),
        ('new_clearance_sale','New Clearance Sale'),
        ('facet','Facet'),
        ('retailers', 'Retailers'),
        ('promotion_offer', 'Promotion Offer'),
        ('promotions', 'Promotions'),
        ('itz_offer','Itz Offers'),
        ('new_arrivals', 'New Arrivals'),
        ('popular_deals', 'Popular Deals'),
        ('eureka', 'Eureka'),
        ('sabse_sasta_sale', 'Sabse Sasta Sale')))
    tab = models.ForeignKey('lists.BattleTab',blank=True,null=True)
    show_default = models.BooleanField(default=False)
    starts_on = models.DateTimeField(blank=True, null=True)
    ends_on = models.DateTimeField(blank=True, null=True)
    sort_order = models.IntegerField(default=1)

    def __unicode__(self):
        if self.tag:
            return self.tag.display_name
        else:
            return '%s - %s' %(self.product, self.type)

class DeliveryTime(models.Model):
    inventory = models.ForeignKey('catalog.Inventory')
    delivery_time = models.PositiveIntegerField(default=7)

    def __unicode__(self):
        return 'Delivery Time for %s = %s' % (self.inventory.rate_chart.product.title, self.delivery_time)

class Pincode(models.Model):
    pin = models.CharField(max_length=6)

    def __unicode__(self):
        return self.pin

class ServicablePincodes(models.Model):
    client = models.ForeignKey('accounts.Client')
    service_type = models.CharField(max_length=20, db_index=True, choices = (
        ('so', 'Ship Local Only'),
        ('otc', 'Over the counter')), default='otc')
    pincode = models.ForeignKey(Pincode)

    def __unicode__(self):
        return '%s - %s - %s' % (self.client.name, self.service_type, self.pincode.pin)

class Inventory(models.Model):
    rate_chart = models.ForeignKey(SellerRateChart, unique=True, related_name='+')
    stock = models.DecimalField(max_digits=7,decimal_places=2,null=True,blank=True,default=0)
    
    def __unicode__(self):
        return 'Stock for %s = %s' % (self.rate_chart.product.title, self.stock)

class ImageVersion(models.Model):
    version = models.DecimalField(max_digits=5, decimal_places=0, null=False, blank=False, default=1)
    product = models.ForeignKey('product')
