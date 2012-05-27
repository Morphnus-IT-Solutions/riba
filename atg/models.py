# Create your models here.
from django.db import models
from django.conf import settings

class DcsCatalog(models.Model):
    catalog = models.CharField(max_length=100,null=True, editable=False, db_column='display_name')               
    catalog_id = models.CharField(primary_key=True,max_length=20,null=False, editable=False, db_column='catalog_id')            

    def __unicode__(self):
        return self.catalog

    class Meta:
        managed = False
        db_table = '%s"dcs_catalog"' % settings.TABLE_PREFIX

class DcsMedia(models.Model):
    media_id = models.CharField(max_length=40, primary_key=True)
    version = models.BigIntegerField()
    creation_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=254, blank=True)
    name = models.CharField(max_length=254)
    path = models.CharField(max_length=254)
    parent_folder_id = models.CharField(max_length=40)
    media_type = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_media"' % settings.TABLE_PREFIX

    def get_image_url(self):
        return '%s/%s' % ('http://images.futurebazaar.com/catalog', self.path)

############### ProductCatalog ###############
# sku_id = DcsCatChldprd.product.sku_id
# category = DcsCatChldprd.category.child_cat.display_name

class FtbManufacturer(models.Model):
    brand_id = models.CharField(max_length=40, primary_key=True)
    brand_name = models.CharField(max_length=256)
    sub_brand_name = models.CharField(max_length=256, blank=True)
    image = models.CharField(max_length=40, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_manufacturer"' % settings.TABLE_PREFIX

class DcsCategory(models.Model):
    category_id = models.CharField(max_length=40, primary_key=True)
    version = models.BigIntegerField()
    catalog = models.ForeignKey(DcsCatalog, null=True, blank=True)
    creation_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    display_name = models.CharField(max_length=254, blank=True)
    description = models.CharField(max_length=254, blank=True)
    long_description = models.TextField(blank=True)
    parent_cat = models.ForeignKey('self', null=True, blank=True)
    category_type = models.BigIntegerField(null=True, blank=True)
    root_category = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_category"' % settings.TABLE_PREFIX

    def get_children(self, add_products=True):
        children = DcsCatChldcat.objects.select_related('child_cat').filter(category=self)
        return [child.child_cat.to_map(add_products) for child in children]

    def get_products(self):
        products = DcsCatChldprd.objects.select_related(
                'product','product__product','product__ftbcodproducts').filter(
                        category=self, product__available_online=1)
        return [p.product.to_map() for p in products]

    def to_map(self, add_products=True):
        data = {
                'category_id': self.category_id,
                'catalog': self.catalog_id,
                'display_name': self.display_name,
                'children': self.get_children(add_products),
                }
        if add_products:
            data['products'] = self.get_products()
        return data


class DcsCatCatalogs(models.Model):
    category = models.ForeignKey(DcsCategory)
    catalog = models.ForeignKey(DcsCatalog)

    class Meta:
        managed = False
        db_table = '%s"dcs_cat_catalogs"' % settings.TABLE_PREFIX

class DcsSku(models.Model):
    sku_id = models.CharField(max_length=40, primary_key=True)
    version = models.BigIntegerField()
    creation_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    display_name = models.CharField(max_length=512, blank=True)
    description = models.CharField(max_length=4000, blank=True)
    sku_type = models.BigIntegerField(null=True, blank=True)
    wholesale_price = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    list_price = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    sale_price = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    on_sale = models.IntegerField(null=True, blank=True)
    tax_status = models.BigIntegerField(null=True, blank=True)
    fulfiller = models.BigIntegerField(null=True, blank=True)
    item_acl = models.CharField(max_length=1024, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_sku"' % settings.TABLE_PREFIX

    def get_prices(self):
        prices = self.dcsprice_set.select_related('price_list').all()
        return [p.to_map() for p in prices]

    def get_mobile_features(self):
        features = {}
        if self.ftbmobilesku_set.all():
            features = self.ftbmobilesku_set.all()[0].to_map()
        if self.ftbmobileskucommunication_set.all():
            features['communications'] = self.ftbmobileskucommunication_set.all()[0].to_map()
        if self.ftbmobileskunetwork_set.all():
            features['networks'] = self.ftbmobileskunetwork_set.all()[0].to_map()
        if self.ftbmobileskukeyfeature_set.all():
            features['keyfeatures'] = self.ftbmobileskukeyfeature_set.all()[0].to_map()
        if self.ftbmobileskutype_set.all():
            features['mobiletype'] = self.ftbmobileskutype_set.all()[0].to_map()
        return features

    def get_computer_features(self):
        features = {}
        if self.ftbcompoffsku_set.all():
            features = self.ftbcompoffsku_set.all()[0].to_map()
        return features

    def get_camera_features(self):
        features = {}
        
        if self.ftbcamerasku_set.all():
            features = self.ftbcamerasku_set.all()[0].to_map()
        return features

    def get_apparel_features(self):
        features = {}
        if self.ftbapparelsku_set.all():
            features = self.ftbapparelsku_set.all()[0].to_map()
        return features

    def get_features(self):
        if self.sku_type == 10:
            return self.get_mobile_features()
        if self.sku_type == 7:
            return self.get_computer_features()
        if self.sku_type == 8:
            return self.get_camera_features()
        if self.sku_type == 2:
            return self.get_apparel_features()


    def to_map(self):
        data = {
            'sku_type': self.sku_type,
            'prices': self.get_prices(),
            'short_desc' : self.description,
                }
        if self.dcsskumedialarge_set.all():
            data['large_images'] = [x.media.get_image_url() for x in 
                    self.dcsskumedialarge_set.all()]
        if self.dcsskumediasmall_set.all():
            data['small_images'] = [x.media.get_image_url() for x in 
                    self.dcsskumediasmall_set.all()]
        if self.dcsskumediathumb_set.all():
            data['thumb_images'] = [x.media.get_image_url() for x in 
                    self.dcsskumediathumb_set.all()]
        data['features'] = self.get_features()
        return data

class DcsSkuCatalogs(models.Model):
    sku = models.ForeignKey(DcsSku)
    catalog = models.ForeignKey(DcsCatalog, primary_key=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_sku_catalogs"' % settings.TABLE_PREFIX


class DcsProduct(models.Model):
    product_id = models.CharField(max_length=40, primary_key=True)
    version = models.BigIntegerField()
    creation_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    display_name = models.CharField(max_length=254, blank=True)
    description = models.CharField(max_length=254, blank=True)
    long_description = models.TextField(blank=True)
    parent_cat_id = models.CharField(max_length=40, blank=True)
    product_type = models.BigIntegerField(null=True, blank=True)
    admin_display = models.CharField(max_length=254, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_product"' % settings.TABLE_PREFIX

    def get_child_skus(self):
        skus = DcsPrdChldsku.objects.select_related(
                'sku',
                'sku__brand',
                'sku__sub_brand',
                'sku__dcspriceset',
                'sku__dcsskumedialarge',
                'sku__dcsskumediasmall',
                'sku__dcsskumediathumb',
                'dcsinventory',
                'sku__dcsskumedialarge__media',
                'sku__dcsskumediasmall__media',
                'sku__dcsskumediathumb__media').filter(
                product = self, sku__available_online = 1)
        return [sku.sku.to_map() for sku in skus]

    def to_map(self, add_skus=True):
        data = {
                'product_id': self.product_id,
                'description': self.description,
                'long_description': self.long_description,
                'display_name': self.display_name,
                'admin_display': self.admin_display, #seems to be empty for all
                'product_type': self.product_type, #seems to be null for all
                }

        if add_skus:
            data['skus'] = self.get_child_skus()

        return data

class FtbColor(models.Model):
    color_id = models.CharField(max_length=40, primary_key=True)
    color_name = models.CharField(max_length=200, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_color"' % settings.TABLE_PREFIX
        
class FtbSku(models.Model):
    sku = models.OneToOneField(DcsSku, primary_key=True)
    article_id = models.CharField(max_length=40)
    brand_name = models.ForeignKey(FtbManufacturer, blank=True, null=True, db_column='brand_name')
    sub_brand_name = models.ForeignKey(FtbManufacturer, blank=True, null=True, related_name='subbrandftbsku_set', db_column='sub_brand_name')
    model_no = models.CharField(max_length=100, blank=True)
    sku_category = models.CharField(max_length=256, blank=True)
    feature = models.CharField(max_length=1024, blank=True)
    style = models.CharField(max_length=256, blank=True)
    manufacturers_part_number = models.CharField(max_length=256, blank=True)
    accessory = models.CharField(max_length=256, blank=True)
    upc = models.CharField(max_length=256, blank=True)
    sku_type = models.CharField(max_length=256, blank=True)
    servicable_city = models.CharField(max_length=256, blank=True)
    unit_size_capacity = models.CharField(max_length=256, blank=True)
    delivery_prom_unit = models.CharField(max_length=100, blank=True)
    display_priority = models.IntegerField(null=True, blank=True)
    description_temp_1 = models.CharField(max_length=4000, blank=True)

    width = models.CharField(max_length=100, blank=True)
    height = models.CharField(max_length=100, blank=True)
    depth = models.CharField(max_length=100, blank=True)
    weight = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=40, blank=True)
    mrp = models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True)
    vendor_rating = models.IntegerField(null=True, blank=True)
    industry_id = models.CharField(max_length=40, blank=True)
    sales_uom = models.CharField(max_length=40, blank=True)
    stockable = models.IntegerField(null=True, blank=True)
    installable = models.IntegerField(null=True, blank=True)
    demo_available = models.IntegerField(null=True, blank=True)

    available_online = models.IntegerField(null=True, blank=True)
    free_shipping = models.IntegerField(null=True, blank=True)
    lucky_price_flag = models.IntegerField(null=True, blank=True)
    size_capacity = models.CharField(max_length=256, blank=True)
    misc1 = models.CharField(max_length=4000, blank=True)
    misc2 = models.CharField(max_length=256, blank=True)
    misc3 = models.CharField(max_length=256, blank=True)
    misc4 = models.CharField(max_length=256, blank=True)
    misc5 = models.CharField(max_length=256, blank=True)
    industrial_id = models.CharField(max_length=256, blank=True)
    listprice_start_date = models.DateField(null=True, blank=True)
    listprice_end_date = models.DateField(null=True, blank=True)
    saleprice_start_date = models.DateField(null=True, blank=True)

    saleprice_end_date = models.DateField(null=True, blank=True)
    mrp_start_date = models.DateField(null=True, blank=True)
    mrp_end_date = models.DateField(null=True, blank=True)
    wholesaleprice_start_date = models.DateField(null=True, blank=True)
    wholesaleprice_end_date = models.DateField(null=True, blank=True)
    weight_uom = models.CharField(max_length=40, blank=True)
    delivery_uom = models.CharField(max_length=40, blank=True)
    invent_check_req = models.IntegerField(null=True, blank=True)
    accept_sap_inven = models.IntegerField(null=True, blank=True)
    base_uom_unit = models.CharField(max_length=100, blank=True)
    delivery_promise = models.IntegerField(null=True, blank=True)
    base_unit_uom = models.CharField(max_length=100, blank=True)
    base_uom = models.CharField(max_length=100, blank=True)
    # This detailed_desc field type is a guess. This is long field in db
    detailed_desc = models.TextField(blank=True)
    no_of_alt_images = models.IntegerField(null=True, blank=True)
    ship_local_only = models.IntegerField(null=True, blank=True)
    home_deliverable = models.IntegerField(null=True, blank=True)
    otc = models.IntegerField(null=True, blank=True)
    local_sku = models.IntegerField(null=True, blank=True)
    import_sku = models.IntegerField(null=True, blank=True)
    kiosk_sku = models.IntegerField(null=True, blank=True)
    internet_only_sku = models.IntegerField(null=True, blank=True)
    discountinued = models.IntegerField(null=True, blank=True)

    back_orderable = models.IntegerField(null=True, blank=True)
    skuquantity_fmi = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_sku"' % settings.TABLE_PREFIX

    def get_inventory(self):
        try:
            inv = self.dcsinventory.to_map()
            if self.back_orderable:
                # if back orderable, we dont need to check stock levels
                # overriding inventory flag
                inv['is_available'] = True
            if self.misc1 == 'D':
                # if product is discontinued, can't sell even if we have stock
                inv['is_available'] = False
            return inv
        except DcsInventory.DoesNotExist:
            if self.invent_check_req == 1:
                return {'is_available': False}
            return {}

    def to_map(self):
        data = {
                'sku_id': self.sku.sku_id,
                'available_online': self.available_online,
                'article_id': self.article_id,
                'otc': self.otc,
                'ship_local_only': self.ship_local_only,
                'misc1' : self.misc1,
                'misc2' : self.misc2,
                'misc3' : self.misc3,
                'misc4' : self.misc4,
                'misc5' : self.misc5,
                'key_features': self.feature,
                'width': self.width,
                'height': self.height,
                'depth': self.depth,
                'weight': self.weight,
                'color': self.color,
                'accessory': self.accessory,
                'model_no': self.model_no,
                }
        if self.brand_name:
            data['brand_name'] = self.brand_name.brand_name
        if self.sub_brand_name:
            data['sub_brand_name'] = self.sub_brand_name.sub_brand_name
        # add info from dcssku
        data.update(self.sku.to_map())
        # add inventory info
        data.update(self.get_inventory())
        try:
            sc = self.ftbskushippingcharge
            data['percent'] = str(sc.percent_of_item_amount)
            data['min_shipping'] = str(sc.minimum_shipping_charge)
            data['max_shipping'] = str(sc.maximum_shipping_charge)
        except FtbSkuShippingCharge.DoesNotExist:
            pass
        except:
            pass
        bundle_items = self.dcsskubndllnk_set.select_related(
                'sku_link').all()

        data['bundle_skus'] = [b.sku_link.bundle_item for b in bundle_items]
        return data

    def get_bundle_skus(self):
        bundle_items = self.dcsskubndllnk_set.select_related(
                'sku_link').all()
        return [b.sku_link for b in bundle_items]



class DcsPrdChldsku(models.Model):
    product = models.ForeignKey(DcsProduct)
    sequence_num = models.BigIntegerField(primary_key=True)
    sku = models.ForeignKey(FtbSku)

    class Meta:
        managed = False
        db_table = '%s"dcs_prd_chldsku"' % settings.TABLE_PREFIX


class FtbCat(models.Model):
    category = models.OneToOneField(DcsCategory, primary_key=True)
    display_priority = models.IntegerField(null=True, blank=True)
    lucky_price_flag = models.IntegerField()
    scene7_flag = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_cat"' % settings.TABLE_PREFIX

    def to_map(self, add_products=True):
        data = self.category.to_map(add_products)
        data['display_priority'] = self.display_priority
        data['scene7_flag'] = self.scene7_flag
        data['lucky_price_flag'] = self.lucky_price_flag
        try:
            sc = self.ftbcatshippingcharge
            data['percent'] = str(sc.percent_of_item_amount)
            data['min_shipping'] = str(sc.minimum_shipping_charge)
            data['max_shipping'] = str(sc.maximum_shipping_charge)
        except FtbCatShippingCharge.DoesNotExist:
            pass
        except:
            pass
        return data

class FtbCatOnline(models.Model):
    category = models.OneToOneField(FtbCat, primary_key=True)
    availlable_online = models.IntegerField()

    class Meta:
        managed = False
        db_table = '%s"ftb_cat_online"' % settings.TABLE_PREFIX

class DcsAllrootCats(models.Model):
    catalog = models.ForeignKey(DcsCatalog, primary_key=True)
    root_cat = models.ForeignKey(FtbCat)

    class Meta:
        managed = False
        db_table = '%s"dcs_allroot_cats"' % settings.TABLE_PREFIX

class DcsCatChldcat(models.Model):
    category = models.ForeignKey(FtbCat)
    sequence_num = models.BigIntegerField(primary_key=True)
    child_cat = models.ForeignKey(FtbCat, related_name='childcategories_set')

    class Meta:
        managed = False
        db_table = '%s"dcs_cat_chldcat"' % settings.TABLE_PREFIX

class FtbProduct(models.Model):
    product = models.ForeignKey(DcsProduct, primary_key=True)
    mc_code = models.CharField(max_length=20)
    third_party = models.IntegerField(null=True, blank=True)
    third_party_vendor = models.CharField(max_length=100, blank=True)
    stockable = models.IntegerField(null=True, blank=True)
    installable = models.IntegerField(null=True, blank=True)
    demo_available = models.IntegerField(null=True, blank=True)
    available_online = models.IntegerField(null=True, blank=True)
    free_shipping = models.IntegerField(null=True, blank=True)
    manufacturer = models.CharField(max_length=40, blank=True)
    material = models.CharField(max_length=100, blank=True)
    misc1 = models.CharField(max_length=100, blank=True)
    misc2 = models.CharField(max_length=100, blank=True)
    misc3 = models.CharField(max_length=100, blank=True)
    misc4 = models.CharField(max_length=100, blank=True)
    misc5 = models.CharField(max_length=100, blank=True)
    article_id = models.CharField(max_length=40, blank=True)
    vendor_id = models.CharField(max_length=40, blank=True)
    display_priority = models.IntegerField(null=True, blank=True)
    #series_style = models.CharField(max_length=100, blank=True)
    lucky_price_flag = models.IntegerField(null=True, blank=True)
    three_sixty_degree = models.IntegerField(null=True, blank=True)
    #related_products = models.CharField(max_length=20, blank=True)
    #product_accessories = models.CharField(max_length=20, blank=True)
    #crosssell_products = models.CharField(max_length=20, blank=True)
    #upsell_products = models.CharField(max_length=20, blank=True)
    #witb_products = models.CharField(max_length=20, blank=True)
    #associated_products = models.CharField(max_length=20, blank=True)
    #recommended_products = models.CharField(max_length=20, blank=True)
    scene7_flag = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_product"' % settings.TABLE_PREFIX

    def to_map(self, add_skus=True):
        data = {
                'article_id': self.article_id,
                'manufacturer': self.manufacturer,
                'misc1': self.misc1,
                'misc2': self.misc2,
                'misc3': self.misc3,
                'misc4': self.misc4,
                'misc5': self.misc5,
                '360_degree': self.three_sixty_degree,
                'available_online': self.available_online
                }
        data.update(self.product.to_map(add_skus))
        try:
            is_cod = self.ftbcodproducts
            data['cod_available'] = True
        except:
            pass
        try:
            sc = self.ftbprdshippingcharge
            data['percent'] = str(sc.percent_of_item_amount)
            data['min_shipping'] = str(sc.minimum_shipping_charge)
            data['max_shipping'] = str(sc.maximum_shipping_charge)
        except FtbPrdShippingCharge.DoesNotExist:
            pass
        except:
            pass
        return data


class DcsPriceList(models.Model):
    price_list_id = models.CharField(max_length=40, primary_key=True)
    version = models.BigIntegerField()
    display_name = models.CharField(max_length=254, blank=True)
    description = models.CharField(max_length=254, blank=True)
    creation_date = models.DateField(null=True, blank=True)
    last_mod_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    locale = models.IntegerField(null=True, blank=True)
    base_price_list = models.CharField(max_length=40, blank=True)
    item_acl = models.CharField(max_length=1024, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_price_list"' % settings.TABLE_PREFIX

class DcsPrice(models.Model):
    price_id = models.CharField(max_length=40, primary_key=True)
    version = models.BigIntegerField()
    price_list = models.ForeignKey(DcsPriceList, db_column='price_list')
    product_id = models.CharField(max_length=40, blank=True)
    sku = models.ForeignKey(DcsSku)
    parent_sku_id = models.CharField(max_length=40, blank=True)
    pricing_scheme = models.BigIntegerField()
    list_price = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    complex_price = models.CharField(max_length=40, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_price"' % settings.TABLE_PREFIX

    def to_map(self):
        return {
                'price': str(self.list_price),
                'price_name': self.price_list.display_name,
                'price_list': self.price_list.price_list_id
                }

class DcsCatChldprd(models.Model):
    category = models.ForeignKey('DcsCategory',unique=True)
    sequence_num = models.BigIntegerField(primary_key=True)
    product = models.ForeignKey('FtbProduct', db_column='child_prd_id')

    class Meta:
        managed = False
        db_table = '%s"dcs_cat_chldprd"' % settings.TABLE_PREFIX

    def __unicode__(self):
        return self.product.product_id

class DcsPrdCatalogs(models.Model):
    product = models.ForeignKey(FtbProduct)
    catalog = models.ForeignKey(DcsCatalog, primary_key=True)
    class Meta:
        managed = False
        db_table = '%s"dcs_prd_catalogs"' % settings.TABLE_PREFIX

class FtbAge(models.Model):
    age_id = models.CharField(max_length=40, primary_key=True)
    age = models.CharField(max_length=256, blank=True)
    age_group_name = models.CharField(max_length=256, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_age"' % settings.TABLE_PREFIX

class FtbApparelSku(models.Model):
    sku = models.ForeignKey(DcsSku, primary_key=True)
    composition = models.CharField(max_length=256, blank=True)
    care_intrustions = models.CharField(max_length=256, blank=True)
    design = models.CharField(max_length=256, blank=True)
    apparel_set = models.CharField(max_length=256, blank=True)
    stitching = models.CharField(max_length=256, blank=True)
    fastening = models.CharField(max_length=256, blank=True)
    embelishment = models.CharField(max_length=256, blank=True)
    apparel_size = models.CharField(max_length=256, blank=True)
    apparel_length = models.CharField(max_length=256, blank=True)
    apparel_front = models.CharField(max_length=256, blank=True)
    apparel_fit = models.CharField(max_length=256, blank=True)
    heel_style = models.CharField(max_length=256, blank=True)
    composition_upper = models.CharField(max_length=256, blank=True)
    composition_lining = models.CharField(max_length=256, blank=True)
    composition_sole = models.CharField(max_length=256, blank=True)
    toe_style = models.CharField(max_length=256, blank=True)
    apparel_strap = models.CharField(max_length=256, blank=True)
    glasses = models.CharField(max_length=256, blank=True)
    apparel_structure = models.CharField(max_length=256, blank=True)
    size_chart = models.CharField(max_length=4000, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_apparel_sku"' % settings.TABLE_PREFIX

    def to_map(self):
        exclude = ['sku']
        d = {}
        for field in self._meta.fields:
            if field.name in exclude:
                continue
            if isinstance(field, models.CharField): type = 'char'
            if isinstance(field, models.DecimalField): type = 'decimal'
            if isinstance(field, models.TextField): type = 'text'
            if isinstance(field, models.IntegerField): type = 'int'
            data = getattr(self, field.name)
            if isinstance(field, models.DecimalField):
                data = str(getattr(self, field.name))
            d[field.name] = {'data': data, 'type': type}
        return d

class FtbBandSku(models.Model):
    band_id = models.CharField(max_length=40, primary_key=True)
    band_colour = models.CharField(max_length=256, blank=True)
    band_material = models.CharField(max_length=500, blank=True)
    band_width = models.CharField(max_length=500, blank=True)
    band_length = models.CharField(max_length=256, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_band_sku"' % settings.TABLE_PREFIX

class FtbCameraSku(models.Model):
    sku = models.ForeignKey(DcsSku, primary_key=True)
    lens = models.CharField(max_length=512, blank=True)
    display_resol = models.CharField(max_length=512, blank=True)
    image_formats = models.CharField(max_length=512, blank=True)
    memory_card_type = models.CharField(max_length=500, blank=True)
    internal_memory = models.CharField(max_length=512, blank=True)
    digital_zoom = models.CharField(max_length=1024, blank=True)
    frame_rate = models.CharField(max_length=512, blank=True)
    display_screen = models.CharField(max_length=512, blank=True)
    camera_accessory = models.CharField(max_length=1024, blank=True)
    design = models.CharField(max_length=512, blank=True)
    mega_pixels = models.CharField(max_length=256, blank=True)
    image_stab = models.IntegerField(null=True, blank=True)
    c_lcd_screen = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    pictbridge_enabled = models.CharField(max_length=256, blank=True)
    movie_mode = models.CharField(max_length=256, blank=True)
    built_in_memory = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    format = models.CharField(max_length=256, blank=True)
    usb_op = models.CharField(max_length=256, blank=True)
    friewire_op = models.CharField(max_length=256, blank=True)
    analog_ip = models.CharField(max_length=500, blank=True)
    optical_zoom = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    digital_zoom_length = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    hd_recording = models.CharField(max_length=256, blank=True)
    ad_ima_sen = models.IntegerField(null=True, blank=True)
    low_light_mode = models.CharField(max_length=512, blank=True)
    built_in_light = models.IntegerField(null=True, blank=True)
    digital_still = models.IntegerField(null=True, blank=True)
    resolution = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    memory_card = models.IntegerField(null=True, blank=True)
    type_camera = models.CharField(max_length=1024, blank=True)
    card_compatibility = models.CharField(max_length=512, blank=True)
    file_formats = models.CharField(max_length=512, blank=True)
    display_modes = models.CharField(max_length=1024, blank=True)
    memory_capacity = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    type_of_memory = models.CharField(max_length=256, blank=True)
    capacity = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    connectivity = models.CharField(max_length=512, blank=True)
    memory_category = models.CharField(max_length=256, blank=True)
    type_of_lense = models.CharField(max_length=512, blank=True)
    filter_size = models.CharField(max_length=512, blank=True)
    aperture_range = models.CharField(max_length=512, blank=True)
    compatible_camera = models.CharField(max_length=500, blank=True)
    wide_angle_panel = models.IntegerField(null=True, blank=True)
    ultra_mounting = models.CharField(max_length=256, blank=True)
    type_of_flash = models.CharField(max_length=512, blank=True)
    adv_features = models.CharField(max_length=256, blank=True)
    tripod_ht_range = models.CharField(max_length=500, blank=True)
    panhead = models.CharField(max_length=256, blank=True)
    remote_control = models.IntegerField(null=True, blank=True)
    audio_formats = models.CharField(max_length=512, blank=True)
    play_back_mode = models.CharField(max_length=512, blank=True)
    composite_interface = models.CharField(max_length=256, blank=True)
    battery_life = models.CharField(max_length=256, blank=True)
    shutter_type = models.CharField(max_length=256, blank=True)
    flash_range = models.CharField(max_length=256, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_camera_sku"' % settings.TABLE_PREFIX

    def to_map(self):
        exclude = ['sku']
        d = {}
        for field in self._meta.fields:
            if field.name in exclude:
                continue
            if isinstance(field, models.CharField): type = 'char'
            if isinstance(field, models.DecimalField): type = 'decimal'
            if isinstance(field, models.TextField): type = 'text'
            if isinstance(field, models.IntegerField): type = 'int'
            data = getattr(self, field.name)
            if isinstance(field, models.DecimalField):
                data = str(getattr(self, field.name))
            d[field.name] = {'data': data, 'type': type}
        return d

class FtbCompOffSku(models.Model):
    sku = models.ForeignKey(DcsSku, primary_key=True)
    processor_speed = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    bus_speed = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    level_cache_two = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    fingerprint_reader = models.CharField(max_length=500, blank=True)
    com_audio = models.IntegerField(null=True, blank=True)
    level_cache_three = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    power_consumption = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    brightness_lumens = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    ram = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    ram_expandable = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    hard_drive_size = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    hard_drive_speed = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    lightscribe = models.IntegerField(null=True, blank=True)
    available_slots = models.CharField(max_length=500, blank=True)
    available_bays = models.CharField(max_length=500, blank=True)
    available_bays1 = models.CharField(max_length=500, blank=True)
    available_pci_slots = models.IntegerField(null=True, blank=True)
    usb = models.CharField(max_length=4, blank=True)
    firewire = models.CharField(max_length=4, blank=True)
    dig_v_interface = models.CharField(max_length=512, blank=True)
    express_card = models.CharField(max_length=500, blank=True)
    s_video_out = models.CharField(max_length=500, blank=True)
    vga = models.CharField(max_length=500, blank=True)
    media_card_slot = models.IntegerField(null=True, blank=True)
    pc_card = models.CharField(max_length=500, blank=True)
    ir_port = models.CharField(max_length=500, blank=True)
    tv_tuner = models.CharField(max_length=500, blank=True)
    ethernet = models.CharField(max_length=500, blank=True)
    built_in_wireless = models.CharField(max_length=500, blank=True)
    dial_up_modem = models.CharField(max_length=120, blank=True)
    video_memory = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    video_memory_type = models.CharField(max_length=512, blank=True)
    operating_system = models.CharField(max_length=120, blank=True)
    additional_features = models.CharField(max_length=500, blank=True)
    bluetooth = models.IntegerField(null=True, blank=True)
    built_in_webcam = models.IntegerField(null=True, blank=True)
    internet_video_memory = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    screen_size = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    wide_screen = models.IntegerField(null=True, blank=True)
    max_resol = models.IntegerField(null=True, blank=True)
    projn_screen = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    projn_distance = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    native_resol = models.DecimalField(null=True, max_digits=20, decimal_places=5, blank=True)
    printing_method = models.CharField(max_length=35, blank=True)
    speed = models.CharField(max_length=35, blank=True)
    blk_white_speeds = models.CharField(max_length=35, blank=True)
    network_connect = models.CharField(max_length=512, blank=True)
    clr_print_speeds = models.CharField(max_length=35, blank=True)
    usb_port = models.IntegerField(null=True, blank=True)
    parallel_port = models.CharField(max_length=500, blank=True)
    photo_print = models.IntegerField(null=True, blank=True)
    photo_print_speeds = models.CharField(max_length=35, blank=True)
    photo_printers = models.IntegerField(null=True, blank=True)
    lcd_screen = models.IntegerField(null=True, blank=True)
    general_features = models.CharField(max_length=120, blank=True)
    note = models.CharField(max_length=120, blank=True)
    copy_speeds = models.CharField(max_length=35, blank=True)
    color_copy = models.CharField(max_length=35, blank=True)
    burns_dvds = models.CharField(max_length=1024, blank=True)
    com_processor_type = models.CharField(max_length=1024, blank=True)
    form_factor = models.CharField(max_length=1024, blank=True)
    chipset = models.CharField(max_length=1024, blank=True)
    monitor = models.CharField(max_length=1024, blank=True)
    peripheral = models.CharField(max_length=1024, blank=True)
    optical_disk_drive = models.CharField(max_length=1024, blank=True)
    power = models.CharField(max_length=1024, blank=True)
    wired = models.CharField(max_length=1024, blank=True)
    part_type = models.CharField(max_length=1024, blank=True)
    processor_brand = models.CharField(max_length=1024, blank=True)
    processor_type = models.CharField(max_length=1024, blank=True)
    memory_type = models.CharField(max_length=1024, blank=True)
    zoom_control = models.CharField(max_length=1024, blank=True)
    lamp_life = models.CharField(max_length=1024, blank=True)
    blk_white_resol = models.CharField(max_length=1024, blank=True)
    clr_print_resol = models.CharField(max_length=1024, blank=True)
    photo_print_size = models.CharField(max_length=1024, blank=True)
    copy_resolution = models.CharField(max_length=1024, blank=True)
    optical_resolution = models.CharField(max_length=1024, blank=True)
    scanner_type = models.CharField(max_length=1024, blank=True)
    available_pcie_slots = models.CharField(max_length=4000, blank=True)
    storage_hard_drive_type = models.CharField(max_length=500, blank=True)
    brightness = models.CharField(max_length=500, blank=True)
    other_interface = models.CharField(max_length=500, blank=True)
    voltage = models.CharField(max_length=500, blank=True)
    computers_power_consumption = models.CharField(max_length=500, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_comp_off_sku"' % settings.TABLE_PREFIX

    def to_map(self):
        exclude = ['sku']
        d = {}
        for field in self._meta.fields:
            if field.name in exclude:
                continue
            if isinstance(field, models.CharField): type = 'char'
            if isinstance(field, models.DecimalField): type = 'decimal'
            if isinstance(field, models.TextField): type = 'text'
            if isinstance(field, models.IntegerField): type = 'int'
            data = getattr(self, field.name)
            if isinstance(field, models.DecimalField):
                data = str(getattr(self, field.name))
            d[field.name] = {'data': data, 'type': type}
        return d

class FtbDecorSku(models.Model):
    sku = models.ForeignKey(FtbSku, max_length=40, primary_key=True)
    art_style = models.CharField(max_length=1024, blank=True)
    horizontal_vertical = models.CharField(max_length=1024, blank=True)
    artist = models.CharField(max_length=1024, blank=True)
    medium = models.CharField(max_length=1024, blank=True)
    frame_color = models.CharField(max_length=1024, blank=True)
    frame_construction = models.CharField(max_length=1024, blank=True)
    frame_finish = models.CharField(max_length=1024, blank=True)
    matted = models.IntegerField(null=True, blank=True)
    mat_color = models.IntegerField(null=True, blank=True)
    face_material = models.CharField(max_length=1024, blank=True)
    water_safe = models.IntegerField(null=True, blank=True)
    suggested_use = models.CharField(max_length=1024, blank=True)
    surface_material = models.CharField(max_length=1024, blank=True)
    basic_care = models.CharField(max_length=1024, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_decor_sku"' % settings.TABLE_PREFIX

    def to_map(self):
        exclude = ['sku']
        d = {}
        for field in self._meta.fields:
            if field.name in exclude:
                continue
            if isinstance(field, models.CharField): type = 'char'
            if isinstance(field, models.DecimalField): type = 'decimal'
            if isinstance(field, models.TextField): type = 'text'
            if isinstance(field, models.IntegerField): type = 'int'
            data = getattr(self, field.name)
            if isinstance(field, models.DecimalField):
                data = str(getattr(self, field.name))
            d[field.name] = {'data': data, 'type': type}
        return d

class FtbMobileCommunication(models.Model):
    communication_id = models.CharField(max_length=40, primary_key=True)
    communication_name = models.CharField(max_length=256, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mobile_communication"' % settings.TABLE_PREFIX

class FtbMobileKeyFeature(models.Model):
    key_feature_id = models.CharField(max_length=40, primary_key=True)
    key_feature_name = models.CharField(max_length=256, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mobile_key_feature"' % settings.TABLE_PREFIX

class FtbMobileNetwork(models.Model):
    network_id = models.CharField(max_length=40, primary_key=True)
    network_name = models.CharField(max_length=256, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mobile_network' % settings.TABLE_PREFIX

class FtbMobileSku(models.Model):
    sku = models.ForeignKey(DcsSku, primary_key=True)
    mobile_talk_time = models.CharField(max_length=256, blank=True)
    mobile_material = models.CharField(max_length=256, blank=True)
    mobile_display = models.CharField(max_length=256, blank=True)
    resolution = models.CharField(max_length=256, blank=True)
    display_size = models.CharField(max_length=256, blank=True)
    memory = models.CharField(max_length=64, blank=True)
    mobile_ring_tones = models.CharField(max_length=256, blank=True)
    camera = models.CharField(max_length=256, blank=True)
    shippping_weight = models.CharField(max_length=64, blank=True)
    mobile_power = models.CharField(max_length=64, blank=True)
    border = models.CharField(max_length=256, blank=True)
    mobile_dimensions = models.CharField(max_length=256, blank=True)
    voice_recorder = models.IntegerField(null=True, blank=True)
    camera_resolution = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    camera_lens_type = models.CharField(max_length=256, blank=True)
    camera_auto_focus = models.IntegerField(null=True, blank=True)
    camera_flash_type = models.CharField(max_length=256, blank=True)
    fm_radio = models.IntegerField(null=True, blank=True)
    music_player = models.IntegerField(null=True, blank=True)
    video_player = models.IntegerField(null=True, blank=True)
    video_format = models.CharField(max_length=256, blank=True)
    video_recording = models.CharField(max_length=256, blank=True)
    gprs = models.CharField(max_length=256, blank=True)
    hscsd = models.CharField(max_length=256, blank=True)
    wap = models.CharField(max_length=256, blank=True)
    edge = models.CharField(max_length=256, blank=True)
    three_g = models.CharField(max_length=256, blank=True)
    wifi = models.CharField(max_length=256, blank=True)
    bluetooth = models.CharField(max_length=256, blank=True)
    infrared = models.CharField(max_length=256, blank=True)
    usbport = models.CharField(max_length=256, blank=True)
    othrs = models.CharField(max_length=256, blank=True)
    other_features_internet = models.CharField(max_length=256, blank=True)
    other_features_games = models.CharField(max_length=256, blank=True)
    other_features_gps = models.CharField(max_length=256, blank=True)
    other_features_messaging = models.CharField(max_length=256, blank=True)
    other_features_others = models.CharField(max_length=512, blank=True)
    alert_types = models.CharField(max_length=256, blank=True)
    operating_system = models.CharField(max_length=256, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mobile_sku"' % settings.TABLE_PREFIX

    def to_map(self):
        exclude = ['sku']
        d = {}
        for field in self._meta.fields:
            if field.name in exclude:
                continue
            if isinstance(field, models.CharField): type = 'char'
            if isinstance(field, models.DecimalField): type = 'decimal'
            if isinstance(field, models.TextField): type = 'text'
            if isinstance(field, models.IntegerField): type = 'int'
            data = getattr(self, field.name)
            if isinstance(field, models.DecimalField):
                data = str(getattr(self, field.name))
            d[field.name] = {'data': data, 'type': type}
        return d


class FtbMobileSkuCommunication(models.Model):
    sku = models.ForeignKey(DcsSku)
    communication = models.ForeignKey(FtbMobileCommunication, primary_key=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mobile_sku_communication"' % settings.TABLE_PREFIX

    def to_map(self):
        return {'type': 'char', 'data': self.communication.communication_name}

class FtbMobileSkuKeyFeature(models.Model):
    sku = models.ForeignKey(DcsSku)
    key_feature = models.ForeignKey(FtbMobileKeyFeature, primary_key=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mobile_sku_key_feature"' % settings.TABLE_PREFIX

    def to_map(self):
        return {'type':'char', 'data': self.key_feature.key_feature_name}

class FtbMobileSkuNetwork(models.Model):
    sku = models.ForeignKey(DcsSku)
    network = models.ForeignKey(FtbMobileNetwork, primary_key=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mobile_sku_network"' % settings.TABLE_PREFIX

    def to_map(self):
        return {}
        return {'type':'char','data': self.network.network_name}

class FtbMobileType(models.Model):
    type_id = models.CharField(max_length=40, primary_key=True)
    type_name = models.CharField(max_length=256, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mobile_type"' % settings.TABLE_PREFIX

class FtbMobileSkuType(models.Model):
    sku = models.ForeignKey(DcsSku)
    type = models.ForeignKey(FtbMobileType, primary_key=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mobile_sku_type"' % settings.TABLE_PREFIX

    def to_map(self):
        return {'type': 'char', 'data': self.type.type_name}


class FtbMovieMusicSku(models.Model):
    sku_id = models.CharField(max_length=40, primary_key=True)
    artist = models.CharField(max_length=256, blank=True)
    actors = models.CharField(max_length=256, blank=True)
    directors = models.CharField(max_length=256, blank=True)
    format = models.CharField(max_length=256, blank=True)
    language = models.CharField(max_length=256, blank=True)
    region = models.CharField(max_length=256, blank=True)
    number_of_discs = models.IntegerField(null=True, blank=True)
    release_date = models.CharField(max_length=256, blank=True)
    run_time = models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True)
    pre_order = models.IntegerField(null=True, blank=True)
    genere = models.CharField(max_length=256, blank=True)
    dubbed = models.CharField(max_length=256, blank=True)
    label = models.CharField(max_length=256, blank=True)
    number_of_tracks = models.IntegerField(null=True, blank=True)
    sub_titles = models.CharField(max_length=256, blank=True)
    req_blu_ray_comp_player = models.IntegerField(null=True, blank=True)
    sound = models.CharField(max_length=256, blank=True)
    rating = models.CharField(max_length=10, blank=True)
    distributor_studio = models.CharField(max_length=1024, blank=True)
    aspect_ratio = models.CharField(max_length=1024, blank=True)
    number_of_chapters = models.CharField(max_length=1024, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_movie_music_sku"' % settings.TABLE_PREFIX

    def to_map(self):
        exclude = ['sku']
        d = {}
        for field in self._meta.fields:
            if field.name in exclude:
                continue
            if isinstance(field, models.CharField): type = 'char'
            if isinstance(field, models.DecimalField): type = 'decimal'
            if isinstance(field, models.TextField): type = 'text'
            if isinstance(field, models.IntegerField): type = 'int'
            data = getattr(self, field.name)
            if isinstance(field, models.DecimalField):
                data = str(getattr(self, field.name))
            d[field.name] = {'data': data, 'type': type}
        return d

class FtbMp3AudioSku(models.Model):
    sku_id = models.CharField(max_length=40, primary_key=True)
    memory = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    expand_memory = models.IntegerField(null=True, blank=True)
    data_file = models.IntegerField(null=True, blank=True)
    usb_inter = models.IntegerField(null=True, blank=True)
    colour_screen = models.IntegerField(null=True, blank=True)
    video_recording = models.IntegerField(null=True, blank=True)
    digital_tuner = models.IntegerField(null=True, blank=True)
    playlist_editing = models.IntegerField(null=True, blank=True)
    dc_jack = models.IntegerField(null=True, blank=True)
    video_capacity = models.CharField(max_length=1024, blank=True)
    memory_media = models.CharField(max_length=500, blank=True)
    files_supported = models.CharField(max_length=500, blank=True)
    docking_station = models.CharField(max_length=500, blank=True)
    data_types_support = models.CharField(max_length=500, blank=True)
    memory_songs = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    memory_photos = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    memory_video = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    display_screen_size = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    audio_output = models.CharField(max_length=500, blank=True)
    signal_to_noise_ratio = models.CharField(max_length=500, blank=True)
    photo_format = models.CharField(max_length=500, blank=True)
    video_format = models.CharField(max_length=500, blank=True)
    head_phones_yype = models.CharField(max_length=500, blank=True)
    head_phones_frequency_response = models.CharField(max_length=500, blank=True)
    head_phones_impedence = models.CharField(max_length=500, blank=True)
    controls = models.CharField(max_length=500, blank=True)
    equaliser = models.CharField(max_length=500, blank=True)
    power_battery_type = models.CharField(max_length=500, blank=True)
    power_music_playnack_time = models.CharField(max_length=500, blank=True)
    power_video_playback_time = models.CharField(max_length=500, blank=True)
    charging_mode = models.CharField(max_length=500, blank=True)
    charging_duration = models.CharField(max_length=500, blank=True)
    operating_system = models.CharField(max_length=500, blank=True)
    interface_others = models.CharField(max_length=500, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_mp3_audio_sku"' % settings.TABLE_PREFIX

    def to_map(self):
        exclude = ['sku']
        d = {}
        for field in self._meta.fields:
            if field.name in exclude:
                continue
            if isinstance(field, models.CharField): type = 'char'
            if isinstance(field, models.DecimalField): type = 'decimal'
            if isinstance(field, models.TextField): type = 'text'
            if isinstance(field, models.IntegerField): type = 'int'
            data = getattr(self, field.name)
            if isinstance(field, models.DecimalField):
                data = str(getattr(self, field.name))
            d[field.name] = {'data': data, 'type': type}
        return d

class FtbOfficeSku(models.Model):
    sku_id = models.CharField(max_length=40, primary_key=True)
    sheet_capacity = models.CharField(max_length=1024, blank=True)
    clip_size = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    sheet_size = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    cover_material = models.CharField(max_length=1024, blank=True)
    number_of_fasteners = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    capacity = models.CharField(max_length=1024, blank=True)
    rings = models.CharField(max_length=1024, blank=True)
    folder_capacity = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    folder_material = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    expanding = models.IntegerField(null=True, blank=True)
    ruled = models.IntegerField(null=True, blank=True)
    spiral_bound = models.IntegerField(null=True, blank=True)
    card_material = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    machine_compatibility = models.IntegerField(null=True, blank=True)
    acid_free = models.IntegerField(null=True, blank=True)
    number_of_functions = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    numeric_memory_capacity = models.DecimalField(null=True, max_digits=10, decimal_places=3, blank=True)
    last_digit_erase = models.IntegerField(null=True, blank=True)
    automatic_shut_off = models.IntegerField(null=True, blank=True)
    batteries_included = models.IntegerField(null=True, blank=True)
    power_source = models.CharField(max_length=1024, blank=True)
    case_included = models.IntegerField(null=True, blank=True)
    paint_type = models.CharField(max_length=1024, blank=True)
    lock_type = models.CharField(max_length=1024, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_office_sku"' % settings.TABLE_PREFIX

    def to_map(self):
        exclude = ['sku']
        d = {}
        for field in self._meta.fields:
            if field.name in exclude:
                continue
            if isinstance(field, models.CharField): type = 'char'
            if isinstance(field, models.DecimalField): type = 'decimal'
            if isinstance(field, models.TextField): type = 'text'
            if isinstance(field, models.IntegerField): type = 'int'
            data = getattr(self, field.name)
            if isinstance(field, models.DecimalField):
                data = str(getattr(self, field.name))
            d[field.name] = {'data': data, 'type': type}
        return d

class DcsPrdMedia(models.Model):
    product = models.ForeignKey(DcsProduct, max_length=40)
    template_id = models.CharField(max_length=40, blank=True, primary_key=True)
    thumbnail_image_id = models.CharField(max_length=40, blank=True)
    small_image_id = models.CharField(max_length=40, blank=True)
    large_image_id = models.CharField(max_length=40, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_prd_media"' % settings.TABLE_PREFIX

class DcsPrdAuxMedia(models.Model):
    product_id = models.ForeignKey(DcsProduct)
    tag = models.CharField(max_length=42, primary_key=True)
    media_id = models.ForeignKey(DcsMedia)

    class Meta:
        managed = False
        db_table = '%s"dcs_prd_aux_media"' % settings.TABLE_PREFIX

class DcsSkuMedia(models.Model):
    sku = models.ForeignKey(DcsSku, primary_key=True)
    template_id = models.ForeignKey(DcsMedia, blank=True, null=True)
    thumbnail_image_id = models.CharField(max_length=40, blank=True)
    small_image_id = models.CharField(max_length=40, blank=True)
    large_image_id = models.CharField(max_length=40, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_sku_media"' % settings.TABLE_PREFIX

class DcsSkuMediaLarge(models.Model):
    sku = models.ForeignKey(DcsSku)
    media = models.ForeignKey(DcsMedia, primary_key=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_sku_media_large"' % settings.TABLE_PREFIX

class DcsSkuMediaSmall(models.Model):
    sku = models.ForeignKey(DcsSku)
    media = models.ForeignKey(DcsMedia, primary_key=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_sku_media_small"' % settings.TABLE_PREFIX

class DcsSkuMediaThumb(models.Model):
    sku = models.ForeignKey(DcsSku)
    media = models.ForeignKey(DcsMedia, primary_key=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_sku_media_thumb"' % settings.TABLE_PREFIX

class DcsInventory(models.Model):
    inventory_id = models.CharField(max_length=40, primary_key=True)
    version = models.BigIntegerField()
    inventory_lock = models.CharField(max_length=20, blank=True)
    creation_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    display_name = models.CharField(max_length=254, blank=True)
    description = models.CharField(max_length=254, blank=True)
    catalog_ref_id = models.OneToOneField(FtbSku, db_column='catalog_ref_id')
    avail_status = models.BigIntegerField()
    availability_date = models.DateField(null=True, blank=True)
    stock_level = models.BigIntegerField(null=True, blank=True)
    backorder_level = models.BigIntegerField(null=True, blank=True)
    preorder_level = models.BigIntegerField(null=True, blank=True)
    stock_thresh = models.BigIntegerField(null=True, blank=True)
    backorder_thresh = models.BigIntegerField(null=True, blank=True)
    preorder_thresh = models.BigIntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_inventory"' % settings.TABLE_PREFIX

    def has_stock(self):
        stock = self.stock_level
        if self.stock_thresh:
            stock = stock - self.stock_thresh
        return stock

    def to_map(self):
        try:
            return {
                    'stock_level' : self.stock_level,
                    'avail_status' : self.avail_status,
                    'is_available': self.has_stock() > 0 and self.avail_status == 1000
                    }
        except:
            return {}

class FtbCodProducts(models.Model):
    product = models.OneToOneField(FtbProduct, primary_key=True)
    min_qty = models.BigIntegerField()
    max_qty = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = '%s"ftb_cod_products"' % settings.TABLE_PREFIX

class FtbCatShippingCharge(models.Model):
    category = models.OneToOneField(FtbCat, primary_key=True)
    minimum_shipping_charge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    maximum_shipping_charge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    percent_of_item_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_cat_shipping_charge"' % settings.TABLE_PREFIX

class FtbPrdShippingCharge(models.Model):
    product = models.OneToOneField(FtbProduct, primary_key=True)
    minimum_shipping_charge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    maximum_shipping_charge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    percent_of_item_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_prd_shipping_charge"' % settings.TABLE_PREFIX

class FtbSkuShippingCharge(models.Model):
    sku = models.OneToOneField(FtbSku, primary_key=True)
    minimum_shipping_charge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    maximum_shipping_charge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    percent_of_item_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_sku_shipping_charge"' % settings.TABLE_PREFIX


class DcsSkuLink(models.Model):
    sku_link_id = models.CharField(max_length=40, primary_key=True, 
            db_column='sku_link_id')
    version = models.BigIntegerField()
    creation_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    display_name = models.CharField(max_length=254, blank=True)
    description = models.CharField(max_length=254, blank=True)
    quantity = models.BigIntegerField()
    bundle_item = models.CharField(max_length=40)
    item_acl = models.CharField(max_length=1024, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcs_sku_link"' % settings.TABLE_PREFIX

class DcsSkuBndllnk(models.Model):
    sku = models.ForeignKey(FtbSku, primary_key=True)
    sequence_num = models.BigIntegerField()
    sku_link = models.ForeignKey(DcsSkuLink, db_column='sku_link_id', related_name='bundleskus_set')

    class Meta:
        managed = False
        db_table = '%s"dcs_sku_bndllnk"' % settings.TABLE_PREFIX


class FtbDealsLogin(models.Model):
    id = models.BigIntegerField(primary_key=True, db_column='id')
    email_address = models.CharField(max_length=80, blank=True, null=True)
    mobile_number = models.CharField(max_length=80, blank=True, null=True)
    facebook_user = models.BigIntegerField(blank=True, null=True)
    registration_time = models.DateTimeField(blank=True, null=True)
    register_name = models.CharField(max_length=40, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_dealslogin"' % settings.TABLE_PREFIX
    
class OnePageOrder(models.Model):

    id = models.CharField(primary_key=True, max_length = 20, editable=False, db_column='id')
    # !!ftb_onepage_order.agentid
    agent_id = models.CharField(max_length = 100, blank=True, null=True, editable=False, db_column='agentid')
    # !!ftb_onepage_order.orderid
    order_id = models.CharField(max_length = 100, blank=True, null=True, db_column='orderid')

    class Meta:
        managed = False
        db_table = '%s"ftb_onepage_order"' % settings.TABLE_PREFIX

class FtbOrder(models.Model):
    order = models.ForeignKey('DcsppOrder',primary_key=True,db_column='order_id')
    sap_order_id = models.CharField(max_length=40, blank=True)
    sales_doc_type = models.CharField(max_length=100, blank=True)
    sales_channel = models.IntegerField(null=True, blank=True)
    sales_location = models.CharField(max_length=254, blank=True)
    sales_organization = models.CharField(max_length=254, blank=True)
    installable = models.IntegerField(null=True, blank=True)
    demo_available = models.IntegerField(null=True, blank=True)
    refund_amount = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    cancel_order_reason = models.CharField(max_length=40, blank=True)
    receipt_no = models.CharField(max_length=30, blank=True)
    is_institutional = models.IntegerField(null=True, blank=True)
    is_exchangeorder = models.IntegerField(null=True, blank=True)
    return_order_id = models.CharField(max_length=40, blank=True)
    exchange_reason_code = models.CharField(max_length=40, blank=True)
    order_sap_tax = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    ord_misc_field1 = models.CharField(max_length=100, blank=True)
    ord_misc_field2 = models.CharField(max_length=100, blank=True)
    ord_misc_field3 = models.CharField(max_length=100, blank=True)
    ord_misc_field4 = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=40, blank=True,db_column='location_code')         #OrderItem.location
    vat_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    vat_percent = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    shipping_nservicecharge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    external_reference = models.CharField(max_length=100, blank=True)
    internal_state = models.CharField(max_length=200, blank=True)
    sap_error_notes = models.CharField(max_length=4000, blank=True)     #order.sap_error_notes
    order_reason = models.CharField(max_length=4000, blank=True)
    has_third_party = models.IntegerField(null=True, blank=True)
    bp_number = models.CharField(max_length=40, blank=True)
    domain_name = models.CharField(max_length=254, blank=True)
    referer_id = models.CharField(max_length=20, blank=True)
    sap_created_date = models.DateField(null=True, blank=True,db_column="sap_order_date")            #order.sap_created_date
    sap_order_type = models.CharField(max_length=20, blank=True)
    order_header_del_block = models.CharField(max_length=20, blank=True)
    digital_queue_id = models.CharField(max_length=10, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_order"' % settings.TABLE_PREFIX

    def get_payable_amount(self):
        return self.order.get_payable_amount()
    
class DcsppItem(models.Model):
    #OrderItem.commerce_item_id
    commerce_item_id = models.CharField(primary_key=True,max_length=40,blank=True,editable=False,null=False,db_column='commerce_item_id')   
    type_item = models.IntegerField(blank=True,editable=False,null=False,db_column='type')
    version = models.IntegerField(blank=True,editable=False,null=False,db_column='version')
    item_class_type = models.CharField(max_length=40,blank=True,editable=False,null=True,db_column='item_class_type')
    catalog_id = models.CharField(max_length=40,blank=True,editable=False,null=True,db_column='catalog_id') #OrderItem.catalog_id
    sku = models.ForeignKey('FtbSku',blank=True,editable=False,null=True,db_column='catalog_ref_id',related_name="sku_set") #OrderItem.sku_id
    catalog_key = models.CharField(max_length=40,blank=True,editable=False,null=True,db_column='catalog_key')
    product_name = models.ForeignKey('DcsProduct',editable=False,null=True,db_column='product_id') #OrderItem.product_id
    quantity = models.DecimalField(max_digits=19,decimal_places=0,blank=True,editable=False,null=True,db_column='quantity') #OrderItem.quantity
    state = models.CharField(max_length=40,blank=True,editable=False,null=True,db_column='state')           #OrderItem.state
    state_detail = models.CharField(max_length=254,blank=True,editable=False,null=True,db_column='state_detaiL')
    line_item_price = models.ForeignKey('DcsppAmountInfo',blank=True,editable=False,null=True,db_column='price_info')    #OrderItem.line_item_price
    amount_info = models.ForeignKey('DcsppItemPrice',blank=True,editable=False,null=True,db_column='price_info')    #OrderItem.line_item_price
    order = models.ForeignKey('DcsppOrder',blank=True,editable=False,null=True,db_column='order_ref')   #OrderItem.order
    order_pay = models.ForeignKey('DcsppPayGroup',to_field="order_ref",blank=True,editable=False,null=True,db_column='order_ref')   #OrderItem.order
    order_ftb = models.ForeignKey('FtbOrder',blank=True,editable=False,null=True,db_column='order_ref')   #OrderItem.order

    class Meta:
        managed = False
        db_table = '%s"dcspp_item"' % settings.TABLE_PREFIX

class DcsppCreditCard(models.Model):
    payment_group_id = models.CharField(primary_key=True, max_length=40)
    credit_card_number = models.CharField(max_length=40, blank=True)
    credit_card_type = models.CharField(max_length=40, blank=True)
    expiration_month = models.CharField(max_length=20, blank=True)
    exp_day_of_month = models.CharField(max_length=20, blank=True)
    expiration_year = models.CharField(max_length=20, blank=True)
    def __unicode__(self):
        return self.payment_group_id
    class Meta:
        managed = False
        db_table = '%s"dcspp_credit_card"' % settings.TABLE_PREFIX

class DcsppPayGroup(models.Model):
    payment_group_id = models.CharField(max_length=40, primary_key=True)
    payment = models.ForeignKey('DcsppCreditCard',db_column="payment_group_id")
    type = models.BigIntegerField()
    version = models.BigIntegerField()
    paygrp_class_type = models.CharField(max_length=40, blank=True)
    payment_method = models.CharField(max_length=40, blank=True)
    amount = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)    #Order.total
    amount_authorized = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    amount_debited = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    amount_credited = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    currency_code = models.CharField(max_length=10, blank=True)     #OrderItem.currency
    state = models.CharField(max_length=40, blank=True)    # payment_state
    state_detail = models.CharField(max_length=254, blank=True)
    submitted_date = models.DateField(null=True, blank=True)
    order_ref = models.OneToOneField('DcsppOrder', blank=True,unique=True, db_column='order_ref')

    def __unicode__(self):
        return self.payment_method
    class Meta:
        managed = False
        db_table = '%s"dcspp_pay_group"' % settings.TABLE_PREFIX

class DcsppOrderPrice(models.Model):
    amount_info = models.ForeignKey('DcsppAmountInfo', db_column='amount_info_id', primary_key=True)
    raw_subtotal = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    tax = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    shipping = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    manual_adj_total = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcspp_order_price"' % settings.TABLE_PREFIX


class DcsppAmountInfo(models.Model):
    amount_info_id = models.CharField(max_length=40, primary_key=True)
    type = models.IntegerField()
    version = models.IntegerField()
    currency_code = models.CharField(max_length=10, blank=True)
    amount = models.DecimalField(max_digits=19, decimal_places=7, blank=True, null=True)
    discounted = models.DecimalField(max_digits=1,decimal_places=0,blank=True,editable=False,null=True)
    amount_is_final = models.DecimalField(max_digits=1,decimal_places=0,blank=True,editable=False,null=True)

    class Meta:
        managed = False
        db_table = '%s"dcspp_amount_info"' % settings.TABLE_PREFIX

    def __unicode__(self):
        return '%s' % self.amount

class DcsppItemPrice(models.Model):
    amount_info = models.CharField(primary_key=True, max_length=40,db_column='amount_info_id')
    list_price = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)        #OrderItem.list_price
    raw_total_price = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    sale_price = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)        #OrderItem.sale_price
    on_sale = models.IntegerField(null=True, blank=True)
    order_discount = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)    #order.order_discount
    qty_discounted = models.IntegerField(null=True, blank=True)                                     #OrderItem.qty_discounted
    qty_as_qualifier = models.IntegerField(null=True, blank=True)
    price_list = models.CharField(max_length=40, blank=True)
    
    def __unicode__(self):
        return self.amount_info
    class Meta:
        managed = False
        db_table = '%s"dcspp_item_price"' % settings.TABLE_PREFIX


class FtbOrderInfo(models.Model):
    orderid = models.CharField(max_length=256, blank=True)
    deliverynumber = models.CharField(max_length=256, blank=True)
    trackingnumber = models.CharField(max_length=256, blank=True)
    shipcomments = models.CharField(max_length=1024, blank=True)
    itemstate = models.CharField(max_length=256, blank=True)
    invoicenumber = models.CharField(max_length=256, blank=True)
    orderstate = models.CharField(max_length=256, blank=True)
    sapdocumentid = models.CharField(max_length=256, blank=True)
    atgdocumentid = models.CharField(max_length=256, blank=True)
    skuid = models.CharField(max_length=256, blank=True)
    shipmentdate = models.CharField(max_length=256, blank=True)
    orderheader = models.CharField(max_length=256, blank=True)
    quantity = models.CharField(max_length=256, blank=True)
    orderdesc = models.CharField(max_length=2048, blank=True)
    lspcode = models.CharField(max_length=256, blank=True)
    plantid = models.CharField(max_length=256, blank=True)
    invoicedate = models.CharField(max_length=256, blank=True)
    plantaddress = models.CharField(max_length=1024, blank=True)
    consigneeaddress = models.CharField(max_length=1024, blank=True)
    billtoaddress = models.CharField(max_length=1024, blank=True)
    saparticleqty = models.CharField(max_length=256, blank=True)
    saparticleid = models.CharField(max_length=256, blank=True)
    saparticledesc = models.CharField(max_length=1024, blank=True)
    unitprice = models.CharField(max_length=256, blank=True)
    grossamount = models.CharField(max_length=256, blank=True)
    sapshippingcharge = models.CharField(max_length=256, blank=True)
    basicprice = models.CharField(max_length=256, blank=True)
    taxrate = models.CharField(max_length=256, blank=True)
    taxamount = models.CharField(max_length=256, blank=True)
    netsellingvalue = models.CharField(max_length=256, blank=True)
    qtygrandtotal = models.CharField(max_length=256, blank=True)
    netcostgrandtotal = models.CharField(max_length=256, blank=True)
    discount = models.CharField(max_length=256, blank=True)     # discount
    discountdesc = models.CharField(max_length=256, blank=True)
    amountinwords = models.CharField(max_length=1024, blank=True)
    serialnumber = models.CharField(max_length=256, blank=True)
    dispatchedthrough = models.CharField(max_length=256, blank=True)
    bpnumber = models.CharField(max_length=256, blank=True)
    orgstate = models.CharField(max_length=256, blank=True)
    orderstatedetails = models.CharField(max_length=256, blank=True)
    updatestatus = models.CharField(max_length=256, blank=True)
    ts_var = models.CharField(max_length=256, blank=True)
    returnid = models.CharField(max_length=256, blank=True)
    remark = models.CharField(max_length=1024, blank=True)
    deliverydate = models.CharField(max_length=256, blank=True)
    processingtype = models.CharField(max_length=40, blank=True)
    class Meta:
        managed = False
        db_table = '%s"ftb_order_info"' % settings.TABLE_PREFIX

class DcsppShipAddr(models.Model):
    shipping_group = models.ForeignKey('DcsppShipGroup',primary_key=True, max_length=40,db_column="shipping_group_id")
    prefix = models.CharField(max_length=40, blank=True)    #ShippingAddress.prefix
    first_name = models.CharField(max_length=40, blank=True)    #ShippingAddress.prefix.firstname
    middle_name = models.CharField(max_length=40, blank=True)   #shippingAddress.prefix
    last_name = models.CharField(max_length=40, blank=True)     #ShippingAddress.prefix
    suffix = models.CharField(max_length=40, blank=True)
    job_title = models.CharField(max_length=40, blank=True)
    company_name = models.CharField(max_length=40, blank=True)
    address_1 = models.CharField(max_length=150, blank=True)    #ShippingAddress.prefix
    address_2 = models.CharField(max_length=150, blank=True)    #ShippingAddress.prefix
    address_3 = models.CharField(max_length=50, blank=True)     #ShippingAddress.prefix
    city = models.CharField(max_length=40, blank=True)          #ShippingAddress.prefix
    county = models.CharField(max_length=40, blank=True)        #ShippingAddress.prefix
    state = models.ForeignKey('FtbState', blank=True,db_column="state")           #ShippingAddress.state
    postal_code = models.CharField(max_length=10, blank=True)   #ShippingAddress.prefix
    country = models.CharField(max_length=40, blank=True)       #ShippingAddress.prefix 
    phone_number = models.CharField(max_length=40, blank=True)
    fax_number = models.CharField(max_length=40, blank=True)
    email = models.CharField(max_length=255, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcspp_ship_addr"' % settings.TABLE_PREFIX

class DcsppOrder(models.Model):
    order = models.CharField(primary_key=True,max_length=40,null=False,db_column='order_id') #order.order_id
   # order_pay = models.ForeignKey('DcsppPayGroup',to_field="order_ref",primary_key=True,null=False,db_column='order_id') #order.order_id
    type = models.IntegerField(blank=True,editable=False,null=False)
    version = models.IntegerField(blank=True,editable=False,null=False)
    order_class_type = models.CharField(max_length=40,blank=True,editable=False,null=True)
    profile = models.ForeignKey('FtbUser',editable=False,null=True,db_column='profile_id')
    description = models.CharField(max_length=64,blank=True,editable=False,null=True)
    order_state = models.CharField(max_length=40,blank=True,editable=False,null=True,db_column="state")     #order.order_state
    state_detail = models.CharField(max_length=254,blank=True,editable=False,null=True)
    created_by_order = models.CharField(max_length=40,blank=True,editable=False,null=True)
    origin_of_order = models.DecimalField(max_digits=10,decimal_places=0,blank=True,editable=False,null=True)
    atg_creation_date = models.DateTimeField(blank=True,editable=False,null=True,db_column="creation_date")       #order.atg_creation_date
    atg_submitted_date = models.DateTimeField(blank=True,editable=False,null=True,db_column="submitted_date")      #order.atg_submitted_date
    last_modified_date = models.DateTimeField(blank=True,editable=False,null=True)  #order.last_modified_date
    completed_date = models.DateTimeField(blank=True,editable=False,null=True)
    price_info = models.ForeignKey('DcsppOrderPrice',blank=True,editable=False,null=True, db_column='price_info')
    tax_price_info = models.CharField(max_length=40,blank=True,editable=False,null=True)
    explicitly_saved = models.DecimalField(max_digits=1,decimal_places=0,blank=True,editable=False,null=True)

    class Meta:
        managed = False
        db_table = '%s"dcspp_order"' % settings.TABLE_PREFIX
    
    def __unicode__(self):
        return self.order

    _shipping = None
    def get_city_and_pincode(self):
        if self._shipping:
            shipping = self._shipping
        else:
            shipping = DcsppShipGroup.objects.filter(order_ref = self)
            shipping = shipping[0]
            dcspp_addr = DcsppShipAddr.objects.filter(shipping_group=shipping.shipping_group)
            shipping = dcspp_addr
        if shipping:
            shipping = shipping[0]
            return '%s %s' % (shipping.city, shipping.postal_code)
        return None

    def get_agent_name(self):
        qs = self.ftbonepageorder_set.all()
        if qs:
            return qs[0].agentid
        return ''

    def get_payable_amount(self):
        # First try to fetch from paygroup
        try:
            paygroup = self.dcspppaygroup
            if self.dcspppaygroup.amount:
                return self.dcspppaygroup.amount
        except:
            pass

        # If not found in paygroup and if incomplete,
        # then pick from amount info table
        if self.order_state == 'INCOMPLETE':
            return self.price_info.amount_info.amount

        # Pick from price info if above conditions are not met
        amount = self.price_info.raw_subtotal + self.price_info.shipping
        amount = amount - self.price_info.manual_adj_total
        return amount
            


class DcsppShipGroup(models.Model):
    shipping_group = models.CharField(max_length=40, primary_key=True,db_column="shipping_group_id")  # ShippingAddress.shipping_group_id
    type = models.BigIntegerField()
    version = models.BigIntegerField()
    shipgrp_class_type = models.CharField(max_length=40, blank=True)
    shipping_method = models.CharField(max_length=40, blank=True)
    description = models.CharField(max_length=64, blank=True)
    ship_on_date = models.DateField(null=True, blank=True)
    actual_ship_date = models.DateField(null=True, blank=True)
    state = models.CharField(max_length=40, blank=True)
    state_detail = models.CharField(max_length=254, blank=True)
    submitted_date = models.DateField(null=True, blank=True)
    price_info = models.CharField(max_length=40, blank=True)
    order_ref = models.CharField(max_length=40, blank=True)
    def __unicode__(self):
        return self.shipping_group_id
    class Meta:
        managed = False
        db_table = '%s"dcspp_ship_group"' % settings.TABLE_PREFIX

class FtbState(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    state_name = models.CharField(max_length=100, blank=True)
    def __unicode__(self):
        return self.state_name
    class Meta:
        managed = False
        db_table = '%s"ftb_state"' % settings.TABLE_PREFIX

class DcsppShipitemRel(models.Model):
    relationship = models.ForeignKey('DcsppRelationship',primary_key=True, max_length=40,db_column='relationship_id')
    shipping_group_id = models.CharField(max_length=40, blank=True)
    commerce_item = models.ForeignKey('DcsppOrderItem',to_field='commerce_items', blank=True,db_column='commerce_item_id')      #ShippingAddress.commerce_item_id
    quantity = models.BigIntegerField(null=True, blank=True)
    returned_qty = models.BigIntegerField(null=True, blank=True)
    amount = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    state = models.CharField(max_length=40, blank=True)
    state_detail = models.CharField(max_length=254, blank=True)
    def __unicode__(self):
        return self.relationship
    class Meta:
        managed = False
        db_table = '%s"dcspp_shipitem_rel"' % settings.TABLE_PREFIX

class DcsppRelationship(models.Model):
    relationship_id = models.CharField(max_length=40, primary_key=True)
    type = models.BigIntegerField()
    version = models.BigIntegerField()
    rel_class_type = models.CharField(max_length=40, blank=True)
    relationship_type = models.CharField(max_length=40, blank=True)
    order_ref = models.CharField(max_length=40, blank=True)
    def __unicode__(self):
        return self.relationship_id
    class Meta:
        managed = False
        db_table = '%s"dcspp_relationship"' % settings.TABLE_PREFIX

############## end ftb_order_ship_addr ##########

############## ftb_plants #############
class FtbPlants(models.Model):
    plant_id = models.CharField(max_length=20, primary_key=True,db_column='plant_id')
    plant_name = models.CharField(max_length=100, blank=True,db_column='plant_name')

    def __unicode__(self):
        return self.plant_name

    class Meta:
        managed = False
        db_table = '%s"ftb_plants"' % settings.TABLE_PREFIX

############ end ftb_plants ###############

########### ftb_order_delitem ###########
class Delivery(models.Model):

    # Ask the view logic to differentiate on cancel_item_reason not being null

    # !!ftb_shipitem_rel.relationship_id
    relationship_id = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='relationship_id') 
    # !!dcspp_order_item.commerce_items
    commerce_item = models.ForeignKey('DcsppItem', blank=True, null=True, editable=False, db_column='commerce_item_id') 
    # !!ftb_delitem_rel.order_id
    order = models.ForeignKey('DcsppOrder', blank=True, null=True, editable=False, db_column='order_id') 
    # !!ftb_delitem_rel.sap_item_id
    sap_item_id = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='sap_item_id') 
    # !!ftb_shipitem_rel.catalog_ref_id
#    del_sku_id = models.CharField(max_length=50, blank=True, null=True, editable=False, db_column='del_sku_id') 
    # !!ftb_shipitem_rel.catalog_ref_id (based on case)
#    ship_sku_id = models.CharField(max_length=50, blank=True, null=True, editable=False, db_column='ship_sku_id') 
    # !!ftb_delitem_rel.tracking_number
    tracking_number = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='tracking_number') 
    # !!ftb_delitem_rel.primary_sap_item_id
    primary_sap_item_id = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='primary_sap_item_id') 
    # !!ftb_delitem_rel.delivery_id
    delivery_id = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='delivery_id') 
    # !!ftb_delitem_rel.invoice_number
    invoice_number = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='invoice_number')

    # !!ftb_delitem_rel.shipping_nservicecharge
    shipping_nservicecharge = models.DecimalField(max_digits=8, decimal_places=2,
            blank=True, null=True, editable=False, db_column='shipping_nservicecharge')
    # !!ftb_delitem_rel.quantity
    quantity = models.IntegerField(blank=True, null=True, editable=False, db_column='quantity')
    # !!ftb_delitem_rel.plant_id
    plant = models.CharField(max_length=20, blank=True, null=True, editable=False, db_column='plant_id')
    # !!ftb_delitem_rel.state
    state = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='state')
    # !!ftb_delitem_rel.lsp_code
    lsp_name = models.CharField(max_length=100, blank=True, null=True, editable=False, db_column='lsp_name')
    
    # !!ftb_delitem_rel.cancel_item_reason
    cancel_item_reason = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='cancel_item_reason')
    # !!ftb_delitem_rel.serial_number
    serial_number = models.IntegerField(blank=True, null=True, editable=False, db_column='serial_number')
    # !!ftb_delitem_rel.dispatched_through
    dispatched_through = models.CharField(max_length=250, blank=True, null=True, editable=False, db_column='dispatched_through')
    # !!dcspp_shipitem_rel.item_rel_misc_field1
    item_price = models.CharField(max_length=100, blank=True, null=True, editable=False, db_column='item_price')

    # !!ftb_delitem_rel.del_item_id
    del_item_id = models.CharField(primary_key=True, max_length=40, blank=True, null=True, editable=False, db_column='del_item_id')

    # !!ftb_delitem_rel.delivery_date
    delivery_date = models.DateField(blank=True, null=True, editable=False, db_column='delivery_date')
    # !!ftb_delitem_rel.invoice_date
    invoice_date = models.DateField(blank=True, null=True, editable=False, db_column='invoice_date')
    # !!ftb_delitem_rel.modified_date
    modified_date = models.DateField(blank=True, null=True, editable=False, db_column='modified_date')
    # !!ftb_delitem_rel.creation_date
    creation_date = models.DateField(blank=True, null=True, editable=False, db_column='creation_date')
    # !!ftb_delitem_rel.cancelled_date
    cancelled_date = models.DateField(blank=True, null=True, editable=False, db_column='cancelled_date')
    # !!ftb_delitem_rel.delivery_create_date
    delivery_create_date = models.DateField(blank=True, null=True, editable=False, db_column='delivery_create_date')
    # !!ftb_delitem_rel.pgi_create_date
    pgi_create_date = models.DateField(blank=True, null=True, editable=False, db_column='pgi_create_date')

    # !!ftb_delitem_rel.delivery_create_by
    delivery_create_by = models.CharField(max_length=100, blank=True, null=True, editable=False, db_column='delivery_create_by')

    # !!ftb_delitem_rel.delivery_type
    delivery_type = models.CharField(max_length=50, blank=True, null=True, editable=False, db_column='delivery_type')
    # !!ftb_delitem_rel.uom
    uom = models.CharField(max_length=100, blank=True, null=True, editable=False, db_column='uom')
    # !!ftb_delitem_rel.invoice_type
    invoice_type = models.CharField(max_length=50, blank=True, null=True, editable=False, db_column='invoice_type')

    def get_expected_date(self):
        if self.invoice_date:
            return self.invoice_date + timedelta(days=5)
        return ''

    class Meta:
        managed = False
        db_table = '%s"fvw_order_delitem"' % settings.TABLE_PREFIX
        verbose_name_plural = 'Deliveries'


class FtbShipitemRel(models.Model):
    relationship = models.ForeignKey('DcsppShipitemRel', primary_key=True,db_column="relationship_id")
    cancel_item_reason = models.CharField(max_length=40, blank=True)
    shipping_cost = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    line_item_amount = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    sap_item_id = models.CharField(max_length=50, blank=True, unique=True)
    catalog_ref_id = models.CharField(max_length=50, blank=True)
    r3_id = models.CharField(max_length=50, blank=True)
    lsp_code = models.CharField(max_length=20, blank=True)
    plant_id = models.CharField(max_length=20, blank=True)
    sku_display_name = models.CharField(max_length=512, blank=True)
    sku_industry_id = models.CharField(max_length=40, blank=True)
    has_third_party = models.IntegerField(null=True, blank=True)
    third_party_vendor = models.CharField(max_length=100, blank=True)
    vendor_id = models.CharField(max_length=40, blank=True)
    service_notes = models.CharField(max_length=200, blank=True)
    acknowledge_details = models.CharField(max_length=200, blank=True)
    gv_claim_codes = models.CharField(max_length=2000, blank=True)
    line_item_sap_tax = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    item_rel_misc_field1 = models.CharField(max_length=100, blank=True)
    item_rel_misc_field2 = models.CharField(max_length=100, blank=True)
    item_rel_misc_field3 = models.CharField(max_length=100, blank=True)
    item_rel_misc_field4 = models.CharField(max_length=100, blank=True)
    bundle_id = models.CharField(max_length=40, blank=True)
    third_party_status = models.CharField(max_length=50, blank=True)
    third_party_notes = models.CharField(max_length=1000, blank=True)
    vat_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    vat_percent = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    shipping_nservicecharge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    req_delivery_date = models.DateField(null=True, blank=True)
    group_location = models.IntegerField(null=True, blank=True)
    group_id = models.CharField(max_length=20, blank=True)
    plants = models.CharField(max_length=512, blank=True)
    total_delivery_time = models.IntegerField(null=True, blank=True)
    wh_processing_time = models.IntegerField(null=True, blank=True)
    lsp_transit_time = models.IntegerField(null=True, blank=True)
    packaging_type = models.CharField(max_length=20, blank=True)
    instructions = models.CharField(max_length=200, blank=True)
    catalog_ids = models.CharField(max_length=100, blank=True)
    mode_of_transport = models.CharField(max_length=100, blank=True)
    shipping_mode = models.CharField(max_length=100, blank=True)
    domain_name = models.CharField(max_length=100, blank=True)
    backorderable = models.IntegerField(null=True, blank=True)
    ship_local_only = models.IntegerField(null=True, blank=True)
    hd = models.IntegerField(null=True, blank=True)
    otc = models.IntegerField(null=True, blank=True)
    sku7ddg = models.IntegerField(null=True, blank=True)
    def __unicode__(self):
        return self.sap_item_id
    class Meta:
        managed = False
        db_table = '%s"ftb_shipitem_rel"' % settings.TABLE_PREFIX

## commerce_item_id = ftbdelitemrel.primary_sap_item_id.relationship_id.commerce_item_id.commerce_items
class FtbDelitemRel(models.Model):
    del_item_id = models.CharField(max_length=40, primary_key=True)
    order = models.ForeignKey("DcsppOrder", blank=True,db_column="order_id")    # Delivery.order
    order_ftb = models.ForeignKey("FtbOrder", to_field='order',blank=True,db_column="order_id")    
    order_pay = models.ForeignKey('DcsppPayGroup',to_field="order_ref",blank=True,editable=False,null=True,db_column='order_id')   #OrderItem.order
    primary_sap_item = models.ForeignKey('FtbShipitemRel',to_field='sap_item_id',blank=True,db_column='primary_sap_item_id')
    sap_item_id = models.CharField(max_length=40, blank=True)
    delivery_id = models.CharField(max_length=40, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    state = models.CharField(max_length=40, blank=True)
    sku = models.ForeignKey('FtbSku', blank=True,db_column='catalog_ref_id')
    invoice_number = models.CharField(max_length=40, blank=True)
    tracking_number = models.CharField(max_length=40, blank=True)
    shipment_date = models.DateField(null=True, blank=True)
    ship_comments = models.CharField(max_length=200, blank=True)
    service_notes = models.CharField(max_length=200, blank=True)
    lsp = models.ForeignKey('FtbLsps', blank=True,db_column='lsp_code')
    cancel_item_reason = models.CharField(max_length=40, blank=True)
    creation_date = models.DateField(null=True, blank=True)
    modified_date = models.DateField(null=True, blank=True)
    invoice_sap_tax = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    del_item_rel_misc_field1 = models.CharField(max_length=100, blank=True)
    del_item_rel_misc_field2 = models.CharField(max_length=100, blank=True)
    del_item_rel_misc_field3 = models.CharField(max_length=100, blank=True)
    del_item_rel_misc_field4 = models.CharField(max_length=100, blank=True)
    vat_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    vat_percent = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    shipping_nservicecharge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    sap_notes = models.CharField(max_length=4000, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    returned_qty = models.IntegerField(null=True, blank=True)
    plant_address = models.CharField(max_length=500, blank=True)
    consignee_address = models.CharField(max_length=500, blank=True)
    bill_to_address = models.CharField(max_length=500, blank=True)
    sap_article_qty = models.IntegerField(null=True, blank=True)
    sap_article_id = models.CharField(max_length=50, blank=True)
    sap_article_desc = models.CharField(max_length=250, blank=True)
    unit_price = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    gross_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    sap_shipping_charge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    basic_price = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    tax_rate = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    tax_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    net_selling_value = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    qty_grand_total = models.IntegerField(null=True, blank=True)
    net_cost_grand_total = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    discount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    discount_desc = models.CharField(max_length=250, blank=True)
    amount_in_words = models.CharField(max_length=500, blank=True)
    dispatched_through = models.CharField(max_length=250, blank=True)
    serial_number = models.IntegerField(null=True, blank=True)
    plant_id = models.CharField(max_length=20, blank=True)
    sap_operation_status = models.CharField(max_length=64, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    plants = models.CharField(max_length=512, blank=True)
    total_delivery_time = models.IntegerField(null=True, blank=True)
    wh_processing_time = models.IntegerField(null=True, blank=True)
    lsp_transit_time = models.IntegerField(null=True, blank=True)
    packaging_type = models.CharField(max_length=20, blank=True)
    instructions = models.CharField(max_length=200, blank=True)
    catalog_ids = models.CharField(max_length=100, blank=True)
    mode_of_transport = models.CharField(max_length=20, blank=True)
    cancelled_date = models.DateField(null=True, blank=True)
    item_del_block = models.CharField(max_length=20, blank=True)
    uom = models.CharField(max_length=20, blank=True)
    item_storage_location = models.CharField(max_length=20, blank=True)
    item_category = models.CharField(max_length=20, blank=True)
    delivery_type = models.CharField(max_length=20, blank=True)
    delivery_create_date = models.DateField(null=True, blank=True)
    delivery_create_by = models.CharField(max_length=100, blank=True)
    invoice_type = models.CharField(max_length=10, blank=True)
    invoice_net_value = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    pgi_create_date = models.DateField(null=True, blank=True)
#    refund_type = models.CharField(max_length=40, blank=True)
#    processing_type = models.CharField(max_length=40, blank=True)
    class Meta:
        managed = False
        db_table = '%s"ftb_delitem_rel"' % settings.TABLE_PREFIX
        verbose_name_plural = 'Deliveries'

class DcsppOrderItem(models.Model):
    order = models.ForeignKey('DcsppOrder',unique=True,db_column="order_id")
    commerce_items = models.ForeignKey('DcsppItem',unique=True,db_column='commerce_items')
    sequence_num = models.BigIntegerField(primary_key=True)
    def __unicode__(self):  
        return '%s' % self.order.order
    class Meta:
        managed = False
        db_table = '%s"dcspp_order_item"' % settings.TABLE_PREFIX

############# end ftb_order_delitem ###########

class CityMap(models.Model):
    pincode = models.CharField(primary_key=True, max_length=6, null=False, editable=False, db_column='pincode')
    city = models.CharField(max_length=20,db_column='city')
    state = models.CharField(max_length=20,db_column='state')
    tier = models.CharField(max_length=20,db_column='tier')
    class Meta:
        managed =False
        db_table = '%s"ftb_pincode_city_map"' % settings.TABLE_PREFIX

class FtbOnepageOrder(models.Model):
    id = models.CharField(max_length=254, primary_key=True)
    agentid = models.CharField(max_length=254, blank=True)
    order = models.ForeignKey('DcsppOrder', blank=True,db_column='orderid')
    create_date = models.DateTimeField(null=True, blank=True)
    def __unicode__(self):
        return self.id
    class Meta:
        managed = False
        db_table = '%s"ftb_onepage_order"' % settings.TABLE_PREFIX

class FtbLsps(models.Model):
    lsp_code = models.CharField(max_length=20, primary_key=True)
    lsp_name = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.lsp_name
    class Meta:
        managed = False
        db_table = '%s"ftb_lsps"' % settings.TABLE_PREFIX

class DcsppShipAddr(models.Model):
    shipping_group = models.ForeignKey('DcsppShipGroup',primary_key=True, max_length=40,db_column="shipping_group_id")
    prefix = models.CharField(max_length=40, blank=True)    #ShippingAddress.prefix
    first_name = models.CharField(max_length=40, blank=True)    #ShippingAddress.prefix.firstname
    middle_name = models.CharField(max_length=40, blank=True)   #shippingAddress.prefix
    last_name = models.CharField(max_length=40, blank=True)     #ShippingAddress.prefix
    suffix = models.CharField(max_length=40, blank=True)
    job_title = models.CharField(max_length=40, blank=True)
    company_name = models.CharField(max_length=40, blank=True)
    address_1 = models.CharField(max_length=150, blank=True)    #ShippingAddress.prefix
    address_2 = models.CharField(max_length=150, blank=True)    #ShippingAddress.prefix
    address_3 = models.CharField(max_length=50, blank=True)     #ShippingAddress.prefix
    city = models.CharField(max_length=40, blank=True)          #ShippingAddress.prefix
    county = models.CharField(max_length=40, blank=True)        #ShippingAddress.prefix
    state = models.ForeignKey('FtbState', blank=True,db_column="state")           #ShippingAddress.state
    postal_code = models.CharField(max_length=10, blank=True)   #ShippingAddress.prefix
    country = models.CharField(max_length=40, blank=True)       #ShippingAddress.prefix 
    phone_number = models.CharField(max_length=40, blank=True)
    fax_number = models.CharField(max_length=40, blank=True)
    email = models.CharField(max_length=255, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dcspp_ship_addr"' % settings.TABLE_PREFIX

class DcsppOrder(models.Model):
    order = models.CharField(primary_key=True,max_length=40,null=False,db_column='order_id') #order.order_id
   # order_pay = models.ForeignKey('DcsppPayGroup',to_field="order_ref",primary_key=True,null=False,db_column='order_id') #order.order_id
    type = models.IntegerField(blank=True,editable=False,null=False)
    version = models.IntegerField(blank=True,editable=False,null=False)
    order_class_type = models.CharField(max_length=40,blank=True,editable=False,null=True)
    profile = models.ForeignKey('FtbUser',editable=False,null=True,db_column='profile_id')
    description = models.CharField(max_length=64,blank=True,editable=False,null=True)
    order_state = models.CharField(max_length=40,blank=True,editable=False,null=True,db_column="state")     #order.order_state
    state_detail = models.CharField(max_length=254,blank=True,editable=False,null=True)
    created_by_order = models.CharField(max_length=40,blank=True,editable=False,null=True)
    origin_of_order = models.DecimalField(max_digits=10,decimal_places=0,blank=True,editable=False,null=True)
    atg_creation_date = models.DateTimeField(blank=True,editable=False,null=True,db_column="creation_date")       #order.atg_creation_date
    atg_submitted_date = models.DateTimeField(blank=True,editable=False,null=True,db_column="submitted_date")      #order.atg_submitted_date
    last_modified_date = models.DateTimeField(blank=True,editable=False,null=True)  #order.last_modified_date
    completed_date = models.DateTimeField(blank=True,editable=False,null=True)
    price_info = models.CharField(max_length=40,blank=True,editable=False,null=True)
    tax_price_info = models.CharField(max_length=40,blank=True,editable=False,null=True)
    explicitly_saved = models.DecimalField(max_digits=1,decimal_places=0,blank=True,editable=False,null=True)

    class Meta:
        managed = False
        db_table = '%s"dcspp_order"' % settings.TABLE_PREFIX
    
    def __unicode__(self):
        return self.order

    _shipping = None
    def get_city_and_pincode(self):
        if self._shipping:
            shipping = self._shipping
        else:
            shipping = DcsppShipGroup.objects.filter(order_ref = self)
            shipping = shipping[0]
            dcspp_addr = DcsppShipAddr.objects.filter(shipping_group=shipping.shipping_group)
            shipping = dcspp_addr
        if shipping:
            shipping = shipping[0]
            return '%s %s' % (shipping.city, shipping.postal_code)
        return None

    def get_agent_name(self):
        qs = self.ftbonepageorder_set.all()
        if qs:
            return qs[0].agentid
        return ''


class DcsppShipGroup(models.Model):
    shipping_group = models.CharField(max_length=40, primary_key=True,db_column="shipping_group_id")  # ShippingAddress.shipping_group_id
    type = models.BigIntegerField()
    version = models.BigIntegerField()
    shipgrp_class_type = models.CharField(max_length=40, blank=True)
    shipping_method = models.CharField(max_length=40, blank=True)
    description = models.CharField(max_length=64, blank=True)
    ship_on_date = models.DateField(null=True, blank=True)
    actual_ship_date = models.DateField(null=True, blank=True)
    state = models.CharField(max_length=40, blank=True)
    state_detail = models.CharField(max_length=254, blank=True)
    submitted_date = models.DateField(null=True, blank=True)
    price_info = models.CharField(max_length=40, blank=True)
    order_ref = models.CharField(max_length=40, blank=True)
    def __unicode__(self):
        return self.shipping_group_id
    class Meta:
        managed = False
        db_table = '%s"dcspp_ship_group"' % settings.TABLE_PREFIX

class FtbState(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    state_name = models.CharField(max_length=100, blank=True)
    def __unicode__(self):
        return self.state_name
    class Meta:
        managed = False
        db_table = '%s"ftb_state"' % settings.TABLE_PREFIX

class DcsppShipitemRel(models.Model):
    relationship = models.ForeignKey('DcsppRelationship',primary_key=True, max_length=40,db_column='relationship_id')
    shipping_group_id = models.CharField(max_length=40, blank=True)
    commerce_item = models.ForeignKey('DcsppOrderItem',to_field='commerce_items', blank=True,db_column='commerce_item_id')      #ShippingAddress.commerce_item_id
    quantity = models.BigIntegerField(null=True, blank=True)
    returned_qty = models.BigIntegerField(null=True, blank=True)
    amount = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    state = models.CharField(max_length=40, blank=True)
    state_detail = models.CharField(max_length=254, blank=True)
    def __unicode__(self):
        return self.relationship
    class Meta:
        managed = False
        db_table = '%s"dcspp_shipitem_rel"' % settings.TABLE_PREFIX

class DcsppRelationship(models.Model):
    relationship_id = models.CharField(max_length=40, primary_key=True)
    type = models.BigIntegerField()
    version = models.BigIntegerField()
    rel_class_type = models.CharField(max_length=40, blank=True)
    relationship_type = models.CharField(max_length=40, blank=True)
    order_ref = models.CharField(max_length=40, blank=True)
    def __unicode__(self):
        return self.relationship_id
    class Meta:
        managed = False
        db_table = '%s"dcspp_relationship"' % settings.TABLE_PREFIX

############## end ftb_order_ship_addr ##########

############## ftb_plants #############
class FtbPlants(models.Model):
    plant_id = models.CharField(max_length=20, primary_key=True,db_column='plant_id')
    plant_name = models.CharField(max_length=100, blank=True,db_column='plant_name')

    def __unicode__(self):
        return self.plant_name

    class Meta:
        managed = False
        db_table = '%s"ftb_plants"' % settings.TABLE_PREFIX

############ end ftb_plants ###############

########### ftb_order_delitem ###########
class Delivery(models.Model):

    # Ask the view logic to differentiate on cancel_item_reason not being null

    # !!ftb_shipitem_rel.relationship_id
    relationship_id = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='relationship_id') 
    # !!dcspp_order_item.commerce_items
    commerce_item = models.ForeignKey('DcsppItem', blank=True, null=True, editable=False, db_column='commerce_item_id') 
    # !!ftb_delitem_rel.order_id
    order = models.ForeignKey('DcsppOrder', blank=True, null=True, editable=False, db_column='order_id') 
    # !!ftb_delitem_rel.sap_item_id
    sap_item_id = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='sap_item_id') 
    # !!ftb_shipitem_rel.catalog_ref_id
#    del_sku_id = models.CharField(max_length=50, blank=True, null=True, editable=False, db_column='del_sku_id') 
    # !!ftb_shipitem_rel.catalog_ref_id (based on case)
#    ship_sku_id = models.CharField(max_length=50, blank=True, null=True, editable=False, db_column='ship_sku_id') 
    # !!ftb_delitem_rel.tracking_number
    tracking_number = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='tracking_number') 
    # !!ftb_delitem_rel.primary_sap_item_id
    primary_sap_item_id = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='primary_sap_item_id') 
    # !!ftb_delitem_rel.delivery_id
    delivery_id = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='delivery_id') 
    # !!ftb_delitem_rel.invoice_number
    invoice_number = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='invoice_number')

    # !!ftb_delitem_rel.shipping_nservicecharge
    shipping_nservicecharge = models.DecimalField(max_digits=8, decimal_places=2,
            blank=True, null=True, editable=False, db_column='shipping_nservicecharge')
    # !!ftb_delitem_rel.quantity
    quantity = models.IntegerField(blank=True, null=True, editable=False, db_column='quantity')
    # !!ftb_delitem_rel.plant_id
    plant = models.CharField(max_length=20, blank=True, null=True, editable=False, db_column='plant_id')
    # !!ftb_delitem_rel.state
    state = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='state')
    # !!ftb_delitem_rel.lsp_code
    lsp_name = models.CharField(max_length=100, blank=True, null=True, editable=False, db_column='lsp_name')
    
    # !!ftb_delitem_rel.cancel_item_reason
    cancel_item_reason = models.CharField(max_length=40, blank=True, null=True, editable=False, db_column='cancel_item_reason')
    # !!ftb_delitem_rel.serial_number
    serial_number = models.IntegerField(blank=True, null=True, editable=False, db_column='serial_number')
    # !!ftb_delitem_rel.dispatched_through
    dispatched_through = models.CharField(max_length=250, blank=True, null=True, editable=False, db_column='dispatched_through')
    # !!dcspp_shipitem_rel.item_rel_misc_field1
    item_price = models.CharField(max_length=100, blank=True, null=True, editable=False, db_column='item_price')

    # !!ftb_delitem_rel.del_item_id
    del_item_id = models.CharField(primary_key=True, max_length=40, blank=True, null=True, editable=False, db_column='del_item_id')

    # !!ftb_delitem_rel.delivery_date
    delivery_date = models.DateField(blank=True, null=True, editable=False, db_column='delivery_date')
    # !!ftb_delitem_rel.invoice_date
    invoice_date = models.DateField(blank=True, null=True, editable=False, db_column='invoice_date')
    # !!ftb_delitem_rel.modified_date
    modified_date = models.DateField(blank=True, null=True, editable=False, db_column='modified_date')
    # !!ftb_delitem_rel.creation_date
    creation_date = models.DateField(blank=True, null=True, editable=False, db_column='creation_date')
    # !!ftb_delitem_rel.cancelled_date
    cancelled_date = models.DateField(blank=True, null=True, editable=False, db_column='cancelled_date')
    # !!ftb_delitem_rel.delivery_create_date
    delivery_create_date = models.DateField(blank=True, null=True, editable=False, db_column='delivery_create_date')
    # !!ftb_delitem_rel.pgi_create_date
    pgi_create_date = models.DateField(blank=True, null=True, editable=False, db_column='pgi_create_date')

    # !!ftb_delitem_rel.delivery_create_by
    delivery_create_by = models.CharField(max_length=100, blank=True, null=True, editable=False, db_column='delivery_create_by')

    # !!ftb_delitem_rel.delivery_type
    delivery_type = models.CharField(max_length=50, blank=True, null=True, editable=False, db_column='delivery_type')
    # !!ftb_delitem_rel.uom
    uom = models.CharField(max_length=100, blank=True, null=True, editable=False, db_column='uom')
    # !!ftb_delitem_rel.invoice_type
    invoice_type = models.CharField(max_length=50, blank=True, null=True, editable=False, db_column='invoice_type')

    def get_expected_date(self):
        if self.invoice_date:
            return self.invoice_date + timedelta(days=5)
        return ''

    class Meta:
        managed = False
        db_table = '%s"fvw_order_delitem"' % settings.TABLE_PREFIX
        verbose_name_plural = 'Deliveries'


class FtbShipitemRel(models.Model):
    relationship = models.ForeignKey('DcsppShipitemRel', primary_key=True,db_column="relationship_id")
    cancel_item_reason = models.CharField(max_length=40, blank=True)
    shipping_cost = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    line_item_amount = models.DecimalField(null=True, max_digits=19, decimal_places=7, blank=True)
    sap_item_id = models.CharField(max_length=50, blank=True, unique=True)
    catalog_ref_id = models.CharField(max_length=50, blank=True)
    r3_id = models.CharField(max_length=50, blank=True)
    lsp_code = models.CharField(max_length=20, blank=True)
    plant_id = models.CharField(max_length=20, blank=True)
    sku_display_name = models.CharField(max_length=512, blank=True)
    sku_industry_id = models.CharField(max_length=40, blank=True)
    has_third_party = models.IntegerField(null=True, blank=True)
    third_party_vendor = models.CharField(max_length=100, blank=True)
    vendor_id = models.CharField(max_length=40, blank=True)
    service_notes = models.CharField(max_length=200, blank=True)
    acknowledge_details = models.CharField(max_length=200, blank=True)
    gv_claim_codes = models.CharField(max_length=2000, blank=True)
    line_item_sap_tax = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    item_rel_misc_field1 = models.CharField(max_length=100, blank=True)
    item_rel_misc_field2 = models.CharField(max_length=100, blank=True)
    item_rel_misc_field3 = models.CharField(max_length=100, blank=True)
    item_rel_misc_field4 = models.CharField(max_length=100, blank=True)
    bundle_id = models.CharField(max_length=40, blank=True)
    third_party_status = models.CharField(max_length=50, blank=True)
    third_party_notes = models.CharField(max_length=1000, blank=True)
    vat_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    vat_percent = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    shipping_nservicecharge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    req_delivery_date = models.DateField(null=True, blank=True)
    group_location = models.IntegerField(null=True, blank=True)
    group_id = models.CharField(max_length=20, blank=True)
    plants = models.CharField(max_length=512, blank=True)
    total_delivery_time = models.IntegerField(null=True, blank=True)
    wh_processing_time = models.IntegerField(null=True, blank=True)
    lsp_transit_time = models.IntegerField(null=True, blank=True)
    packaging_type = models.CharField(max_length=20, blank=True)
    instructions = models.CharField(max_length=200, blank=True)
    catalog_ids = models.CharField(max_length=100, blank=True)
    mode_of_transport = models.CharField(max_length=100, blank=True)
    shipping_mode = models.CharField(max_length=100, blank=True)
    domain_name = models.CharField(max_length=100, blank=True)
    backorderable = models.IntegerField(null=True, blank=True)
    ship_local_only = models.IntegerField(null=True, blank=True)
    hd = models.IntegerField(null=True, blank=True)
    otc = models.IntegerField(null=True, blank=True)
    sku7ddg = models.IntegerField(null=True, blank=True)
    def __unicode__(self):
        return self.sap_item_id
    class Meta:
        managed = False
        db_table = '%s"ftb_shipitem_rel"' % settings.TABLE_PREFIX

## commerce_item_id = ftbdelitemrel.primary_sap_item_id.relationship_id.commerce_item_id.commerce_items
class FtbDelitemRel(models.Model):
    del_item_id = models.CharField(max_length=40, primary_key=True)
    order = models.ForeignKey("DcsppOrder", blank=True,db_column="order_id")    # Delivery.order
    order_ftb = models.ForeignKey("FtbOrder", to_field='order',blank=True,db_column="order_id")    
    order_pay = models.ForeignKey('DcsppPayGroup',to_field="order_ref",blank=True,editable=False,null=True,db_column='order_id')   #OrderItem.order
    primary_sap_item = models.ForeignKey('FtbShipitemRel',to_field='sap_item_id',blank=True,db_column='primary_sap_item_id')
    sap_item_id = models.CharField(max_length=40, blank=True)
    delivery_id = models.CharField(max_length=40, blank=True)
    quantity = models.IntegerField(null=True, blank=True)
    state = models.CharField(max_length=40, blank=True)
    sku = models.ForeignKey('FtbSku', blank=True,db_column='catalog_ref_id')
    invoice_number = models.CharField(max_length=40, blank=True)
    tracking_number = models.CharField(max_length=40, blank=True)
    shipment_date = models.DateField(null=True, blank=True)
    ship_comments = models.CharField(max_length=200, blank=True)
    service_notes = models.CharField(max_length=200, blank=True)
    lsp = models.ForeignKey('FtbLsps', blank=True,db_column='lsp_code')
    cancel_item_reason = models.CharField(max_length=40, blank=True)
    creation_date = models.DateField(null=True, blank=True)
    modified_date = models.DateField(null=True, blank=True)
    invoice_sap_tax = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    del_item_rel_misc_field1 = models.CharField(max_length=100, blank=True)
    del_item_rel_misc_field2 = models.CharField(max_length=100, blank=True)
    del_item_rel_misc_field3 = models.CharField(max_length=100, blank=True)
    del_item_rel_misc_field4 = models.CharField(max_length=100, blank=True)
    vat_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    vat_percent = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    shipping_nservicecharge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    sap_notes = models.CharField(max_length=4000, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    returned_qty = models.IntegerField(null=True, blank=True)
    plant_address = models.CharField(max_length=500, blank=True)
    consignee_address = models.CharField(max_length=500, blank=True)
    bill_to_address = models.CharField(max_length=500, blank=True)
    sap_article_qty = models.IntegerField(null=True, blank=True)
    sap_article_id = models.CharField(max_length=50, blank=True)
    sap_article_desc = models.CharField(max_length=250, blank=True)
    unit_price = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    gross_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    sap_shipping_charge = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    basic_price = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    tax_rate = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    tax_amount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    net_selling_value = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    qty_grand_total = models.IntegerField(null=True, blank=True)
    net_cost_grand_total = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    discount = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    discount_desc = models.CharField(max_length=250, blank=True)
    amount_in_words = models.CharField(max_length=500, blank=True)
    dispatched_through = models.CharField(max_length=250, blank=True)
    serial_number = models.IntegerField(null=True, blank=True)
    plant_id = models.CharField(max_length=20, blank=True)
    sap_operation_status = models.CharField(max_length=64, blank=True)
    delivery_date = models.DateField(null=True, blank=True)
    plants = models.CharField(max_length=512, blank=True)
    total_delivery_time = models.IntegerField(null=True, blank=True)
    wh_processing_time = models.IntegerField(null=True, blank=True)
    lsp_transit_time = models.IntegerField(null=True, blank=True)
    packaging_type = models.CharField(max_length=20, blank=True)
    instructions = models.CharField(max_length=200, blank=True)
    catalog_ids = models.CharField(max_length=100, blank=True)
    mode_of_transport = models.CharField(max_length=20, blank=True)
    cancelled_date = models.DateField(null=True, blank=True)
    item_del_block = models.CharField(max_length=20, blank=True)
    uom = models.CharField(max_length=20, blank=True)
    item_storage_location = models.CharField(max_length=20, blank=True)
    item_category = models.CharField(max_length=20, blank=True)
    delivery_type = models.CharField(max_length=20, blank=True)
    delivery_create_date = models.DateField(null=True, blank=True)
    delivery_create_by = models.CharField(max_length=100, blank=True)
    invoice_type = models.CharField(max_length=10, blank=True)
    invoice_net_value = models.DecimalField(null=True, max_digits=8, decimal_places=2, blank=True)
    pgi_create_date = models.DateField(null=True, blank=True)
#    refund_type = models.CharField(max_length=40, blank=True)
#    processing_type = models.CharField(max_length=40, blank=True)
    class Meta:
        managed = False
        db_table = '%s"ftb_delitem_rel"' % settings.TABLE_PREFIX
        verbose_name_plural = 'Deliveries'

class DcsppOrderItem(models.Model):
    order = models.ForeignKey('DcsppOrder',unique=True,db_column="order_id")
    commerce_items = models.ForeignKey('DcsppItem',unique=True,db_column='commerce_items')
    sequence_num = models.BigIntegerField(primary_key=True)
    def __unicode__(self):  
        return '%s' % self.order.order
    class Meta:
        managed = False
        db_table = '%s"dcspp_order_item"' % settings.TABLE_PREFIX

############# end ftb_order_delitem ###########

class CityMap(models.Model):
    pincode = models.CharField(primary_key=True, max_length=6, null=False, editable=False, db_column='pincode')
    city = models.CharField(max_length=20,db_column='city')
    state = models.CharField(max_length=20,db_column='state')
    tier = models.CharField(max_length=20,db_column='tier')
    class Meta:
        managed =False
        db_table = '%s"ftb_pincode_city_map"' % settings.TABLE_PREFIX

class FtbOnepageOrder(models.Model):
    id = models.CharField(max_length=254, primary_key=True)
    agentid = models.CharField(max_length=254, blank=True)
    order = models.ForeignKey('DcsppOrder', blank=True,db_column='orderid')
    create_date = models.DateTimeField(null=True, blank=True)
    def __unicode__(self):
        return self.id
    class Meta:
        managed = False
        db_table = '%s"ftb_onepage_order"' % settings.TABLE_PREFIX

class FtbLsps(models.Model):
    lsp_code = models.CharField(max_length=20, primary_key=True)
    lsp_name = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return self.lsp_name
    class Meta:
        managed = False
        db_table = '%s"ftb_lsps"' % settings.TABLE_PREFIX

class DpsUser(models.Model):
    dps_id = models.CharField(max_length=40, primary_key=True,db_column='id')
    login = models.CharField(unique=True, max_length=40)       # User.login
    auto_login = models.IntegerField(null=True, blank=True)
    password = models.CharField(max_length=35, blank=True)
    member = models.IntegerField(null=True, blank=True)
    first_name = models.CharField(max_length=40, blank=True)    # User.first_name
    middle_name = models.CharField(max_length=40, blank=True)
    last_name = models.CharField(max_length=40, blank=True)     # User.last_name
    user_type = models.BigIntegerField(null=True, blank=True)
    locale = models.BigIntegerField(null=True, blank=True)
    lastactivity_date = models.DateField(null=True, blank=True)
    lastpwdupdate = models.DateField(null=True, blank=True)
    generatedpwd = models.IntegerField(null=True, blank=True)
    registration_date = models.DateField(null=True, blank=True) # User.registration_date
    email = models.CharField(max_length=255, blank=True)
    email_status = models.BigIntegerField(null=True, blank=True)
    receive_email = models.BigIntegerField(null=True, blank=True)   # User.receive_email
    last_emailed = models.DateField(null=True, blank=True)
    gender = models.BigIntegerField(null=True, blank=True)      # User.gender
    date_of_birth = models.DateField(null=True, blank=True)     # User.date_of_birth
    securitystatus = models.BigIntegerField(null=True, blank=True)
    description = models.CharField(max_length=254, blank=True)
    def __unicode__(self):
        return self.dps_id
    class Meta:
        managed =False
        db_table = '%s"dps_user"' % settings.TABLE_PREFIX

class FtbUser(models.Model):
    user = models.ForeignKey('DpsUser',primary_key=True,db_column='id')      # User.id
    dps_info = models.ForeignKey('DpsContactInfo',db_column='id')      # User.id
    title = models.IntegerField(null=True, blank=True)      # User.title
#    hear_about = models.ForeignKey('FtbUsrHearAbout', blank=True)
    martial_status = models.IntegerField(null=True, blank=True) # User.martial_status
#    income_range = models.ForeignKey('FtbUsrIncomeRange', blank=True)  # User,income_range
#    education = models.ForeignKey('FtbUsrEducation', blank=True)     # User.education
#    occupation = models.ForeignKey('FtbUsrOccupation', blank=True)    # User.occupation
    cc_owner = models.BigIntegerField(null=True, blank=True)    # User.cc_owner
    reg_referrer = models.CharField(max_length=100, blank=True) # User.reg_referrer
    reg_adunit = models.CharField(max_length=200, blank=True)   
    reg_campaign_id = models.CharField(max_length=50, blank=True)   # User.reg_campaign_id
    reg_creator = models.CharField(max_length=250, blank=True)
    sap_id = models.CharField(max_length=50, blank=True)        # User.sap_id
    mobile_phone_num = models.CharField(max_length=20, blank=True)  # User.mobile_number
    email_validated = models.BigIntegerField(null=True, blank=True)
    newsletter = models.IntegerField(null=True, blank=True)     # USer.newsletter
    recent_searches = models.CharField(max_length=200, blank=True)
    referrer = models.CharField(max_length=100, blank=True)
    saved_searches = models.CharField(max_length=200, blank=True)
    creator = models.CharField(max_length=250, blank=True)
    promotion_used_code = models.CharField(max_length=250, blank=True)  # User.promotion_used_code
    search_terms = models.CharField(max_length=250, blank=True)
    no_of_orders = models.BigIntegerField(null=True, blank=True)
    order_value = models.BigIntegerField(null=True, blank=True)
    browsed_products = models.CharField(max_length=250, blank=True)
    product_purchased = models.CharField(max_length=250, blank=True)
    loyalty_type = models.CharField(max_length=200, blank=True)
    employee = models.CharField(max_length=40, blank=True)
    store_association = models.CharField(max_length=200, blank=True)
    external_ref_code = models.CharField(max_length=20, blank=True)
#    special_occasion = models.ForeignKey('FtbUsrSpecialOccasion', blank=True)
    user_active = models.IntegerField(null=True, blank=True)    # User.user_active
    bp_number = models.CharField(max_length=40, blank=True)     # User.bp_number
    ezone_city_id = models.CharField(max_length=20, blank=True)
    referer_id = models.CharField(max_length=20, blank=True)
    is_guest_user = models.CharField(max_length=50, blank=True)
    def __unicode__(self):
        return self.user.login

    def get_name(self):
        if self.user.first_name and self.user.last_name:
            return '%s %s' % (self.user.first_name, self.user.last_name)
        return self.user.first_name

    def get_phones(self):
        if self.mobile_phone_num and self.dps_info.phone_number:
            return '%s, %s' % (self.mobile_number, self.dps_info.phone_number)
        if self.mobile_phone_num:
            return self.mobile_phone_num
        if self.dps_info.phone_number:
            return self.dps_info.phone_number
        return ''

    class Meta:
        managed = False
        db_table = '%s"ftb_user"' % settings.TABLE_PREFIX


class DpsUserAddress(models.Model):
    id = models.ForeignKey('DpsUser',primary_key=True)
    home_addr_id = models.CharField(max_length=40, blank=True)
    billing_addr_id = models.CharField(max_length=40, blank=True)
    shipping_addr_id = models.CharField(max_length=40, blank=True)
    class Meta:
        managed = False
        db_table = '%s"dps_user_address"' % settings.TABLE_PREFIX

class DpsContactInfo(models.Model):
    info = models.CharField(max_length=40, primary_key=True,db_column='id')
    user_id = models.CharField(max_length=40, blank=True)
    prefix = models.CharField(max_length=40, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    suffix = models.CharField(max_length=40, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=40, blank=True)
    address1 = models.CharField(max_length=150, blank=True)
    address2 = models.CharField(max_length=150, blank=True)
    address3 = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=20, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    county = models.CharField(max_length=40, blank=True)
    country = models.CharField(max_length=40, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    fax_number = models.CharField(max_length=15, blank=True)
#    phone_std_code = models.CharField(max_length=10, blank=True)


class DpsUserAddress(models.Model):
    id = models.ForeignKey('DpsUser',primary_key=True)
    home_addr_id = models.CharField(max_length=40, blank=True)
    billing_addr_id = models.CharField(max_length=40, blank=True)
    shipping_addr_id = models.CharField(max_length=40, blank=True)

    class Meta:
        managed = False
        db_table = '%s"dps_user_address"' % settings.TABLE_PREFIX

class DpsContactInfo(models.Model):
    info = models.CharField(max_length=40, primary_key=True,db_column='id')
    user_id = models.CharField(max_length=40, blank=True)
    prefix = models.CharField(max_length=40, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    suffix = models.CharField(max_length=40, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    company_name = models.CharField(max_length=40, blank=True)
    address1 = models.CharField(max_length=150, blank=True)
    address2 = models.CharField(max_length=150, blank=True)
    address3 = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=30, blank=True)
    state = models.CharField(max_length=20, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    county = models.CharField(max_length=40, blank=True)
    country = models.CharField(max_length=40, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    fax_number = models.CharField(max_length=15, blank=True)
#    phone_std_code = models.CharField(max_length=10, blank=True)
    def __unicode__(self):
        return self.info

    class Meta:
        managed = False
        db_table = '%s"dps_contact_info"' % settings.TABLE_PREFIX

class FtbDcsDcMaster(models.Model):
    id = models.CharField(max_length=254, primary_key=True, db_column="dc_code")
    dc_name = models.CharField(max_length=254, blank=True)
    dc_type = models.CharField(max_length=20, blank=True)
    otc = models.IntegerField(null=True, blank=True)
    hd = models.IntegerField(null=True, blank=True)
    brand = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=200, blank=True)
    storage_location = models.CharField(max_length=20, blank=True)
    processing_time = models.IntegerField(null=True, blank=True)
    catalog_id = models.CharField(max_length=20, blank=True)
    third_party = models.IntegerField(null=True, blank=True)
    catalogs = models.CharField(max_length=254, blank=True)
    def __unicode__(self):
        return self.id

    class Meta:
        managed = False
        db_table = '%s"ftb_dcs_dc_master"' % settings.TABLE_PREFIX

class FtbDcsDcInventory(models.Model):
    inventory = models.ForeignKey('DcsInventory', db_column='inventory_id', primary_key=True)
    dc_code = models.ForeignKey('FtbDcsDcMaster', db_column="dc_code")
    quantity = models.CharField(max_length=254, blank=True)
    stock_level = models.IntegerField(null=True, blank=True)
    class Meta:
        managed = False
        db_table = '%s"ftb_dcs_dc_inventory"' % settings.TABLE_PREFIX


#Adding additional tables for IFS import
class FtbFlfProductgroupDcs(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    group_id = models.CharField(max_length=20, blank=True)
    dc_code = models.CharField(max_length=20, blank=True)
    active = models.IntegerField(null=True, blank=True)   
    class Meta:
        managed = False
        db_table = '%s"ftb_flf_productgroup_dcs"' % settings.TABLE_PREFIX


class FtbPlantsLspGroups(models.Model):
    id = models.CharField(max_length=40, blank=True, primary_key = True)
    group_id = models.CharField(max_length=10, blank=True)
    pin_code = models.IntegerField(null=True, blank=True)
    plant_id = models.CharField(max_length=20, blank=True)
    lsp_code = models.CharField(max_length=20, blank=True)
    group_location = models.IntegerField(null=True, blank=True)
    shipping_mode = models.CharField(max_length=100, blank=True)
    mode_of_transport = models.CharField(max_length=100, blank=True)
    delivery_guarantee_in_days = models.IntegerField(null=True, blank=True)
    class Meta:
        managed = False
        db_table = '%s"ftb_plants_lsp_groups"' % settings.TABLE_PREFIX

class FtbFlfZipgroupZipcodes(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    zipgroup_id = models.CharField(max_length=20, blank=True)
    zipcode = models.CharField(max_length=20, blank=True)
    zipgroup_name = models.CharField(max_length=50, blank=True)
    class Meta:
        managed = False
        db_table = '%s"ftb_flf_zipgroup_zipcodes"' % settings.TABLE_PREFIX

class FtbFlfZipgroupDcs(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    zipgroup_id = models.CharField(max_length=20, blank=True)
    dc_code = models.CharField(max_length=20, blank=True)
    dc_precedence = models.CharField(max_length=20, blank=True)
    catalog_id = models.CharField(max_length=20, blank=True)
    class Meta:
        managed = False
        db_table = '%s"ftb_flf_zipgroup_dcs"' % settings.TABLE_PREFIX

class FtbPaytypeDcMap(models.Model):
    id = models.CharField(max_length=20, blank=True, primary_key=True)
    pay_type = models.CharField(max_length=40, blank=True)
    dc_id = models.CharField(max_length=40, blank=True)
    class Meta:
        managed = False
        db_table = '%s"ftb_paytpe_dcc_map"' % settings.TABLE_PREFIX

class FtbQuantitycheck(models.Model):
    sku = models.OneToOneField('FtbSku', primary_key=True)
    max_quantity = models.IntegerField(null=True, blank=True)
    min_quantity = models.IntegerField(null=True, blank=True)
    default_quantity = models.IntegerField(null=True, blank=True)
    #special_promcode = models.CharField(max_length=40, blank=True)
    #asset_version = models.BigIntegerField()
    #workspace_id = models.CharField(max_length=40)
    #branch_id = models.CharField(max_length=40)
    #is_head = models.IntegerField()
    #version_deleted = models.IntegerField()
    #version_editable = models.IntegerField()
    #pred_version = models.BigIntegerField(null=True, blank=True)
    #checkin_date = models.DateField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = '%s"ftb_quantitycheck"' % settings.TABLE_PREFIX

