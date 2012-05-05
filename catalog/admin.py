from django.contrib import admin
from categories.models import Feature
from catalog.models import Brand, Product, ProductImage, ProductFeatures,ProductTags, Tag
from categories.models import ProductType
from catalog.models import ProductVariant, Availability, AvailabilityConstraint
from catalog.models import SellerRateChart, ShippingInfo
from django import forms
import logging
from django.db.models import *
log = logging.getLogger('request')

def get_field(self, name, many_to_many=True):
    to_search = many_to_many and (self.fields + self.many_to_many) or self.fields
    if hasattr(self, '_copy_fields'):
        to_search += self._copy_fields
    for f in to_search:
        if f.name == name:
            return f
    if not name.startswith('__') and '__' in name:
        f = None
        model = self
        path = name.split('__')
        for field_name in path:
            f = model._get_field(field_name)
            if isinstance(f, ForeignKey):
                model = f.rel.to._meta
        f = copy.deepcopy(f)
        f.name = name
        if not hasattr(self, "_copy_fields"):
            self._copy_fields = list()
        self._copy_fields.append(f)
        return f
    raise FieldDoesNotExist, '%s has no field named %r' % (self.object_name, name)

setattr(options.Options, '_get_field', options.Options.get_field.im_func)

setattr(options.Options, 'get_field', get_field)


class BrandAdmin(admin.ModelAdmin):
    search_fields = ['name']
    list_display = ('name', 'slug','image')
    list_filter = ('moderate',)
admin.site.register(Brand, BrandAdmin)

class ProductFeaturesAdminForm(forms.ModelForm):
    class Meta:
        model = ProductFeatures

class ProductTypeInline(admin.TabularInline):
    model = ProductType
    extra = 2

class ProductFeaturesInline(admin.TabularInline):
    model = ProductFeatures

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'feature':
            if not request.path.endswith('/add/'):
                id = request.path.split('/')[-2]
                product = Product.objects.get(pk=int(id))
                kwargs['queryset'] = Feature.objects.filter(product_type=product.product_type)
            return db_field.formfield(**kwargs)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2

class SellerRateChartInline(admin.StackedInline):
    exclude = ('condition',)
    model = SellerRateChart
    fieldsets = [
            ('Required',{'fields':['seller','sku','article_id','visibility_status','list_price','transfer_price','offer_price','shipping_charges','stock_status', 'shipping_paid_by', 'payment_charges_paid_by']}),
            ('Optional',{'classes':('collapse',),'fields':['is_prefered','warranty','external_product_id','external_product_link','shipping_duration','cod_charge','payment_collection_charges','gift_title','gift_desc','is_cod_available','cod_available_at','ship_local_only','home_deliverable','otc']})]
    extra = 0

class ShippingInfoInline(admin.TabularInline):
    model = ShippingInfo
    max_num = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    fk_name = 'blueprint' 
    extra = 0

class ProductAdmin(admin.ModelAdmin):
    def update_solr_index(modeladmin, request, queryset):
        for product in queryset:
            product.update_solr_index()

    exclude = ('view_count','pending_order_count','cart_count','confirmed_order_count','meta_description')
    inlines = [ProductFeaturesInline,ProductImageInline,SellerRateChartInline,ShippingInfoInline,ProductVariantInline]
    fieldsets = [
            ('Overview', {'fields':['title','description','currency','brand','model','category','status','has_images','video_embed','type','product_type']}),
            ('SEO',{'fields':['slug']})]
    actions = ['update_solr_index']
    list_display = ('title','category','brand')
    list_filter = ('has_images','status','type','moderate','category','brand')
    search_fields = ['title']

    def response_add(self, request, obj):
        obj.update_solr_index()
        return super(ProductAdmin, self).response_add(request, obj)

    def response_change(self, request, obj):
        obj.update_solr_index()
        return super(ProductAdmin, self).response_change(request, obj)

admin.site.register(Product, ProductAdmin)

class ProductImageAdmin(admin.ModelAdmin):
    pass
admin.site.register(ProductImage, ProductImageAdmin)


class ProductFeaturesAdmin(admin.ModelAdmin):
    search_fields = ['product__title']
    list_display = ('product','feature','data')
admin.site.register(ProductFeatures, ProductFeaturesAdmin)

class ProductVariantAdmin(admin.ModelAdmin):
    search_fields = ['blueprint__title','variant__title']
    list_display = ('blueprint','variant','is_default_product')
admin.site.register(ProductVariant, ProductVariantAdmin)

class AvailabilityConstraintInline(admin.TabularInline):
    extra = 1
    from django import forms
    from django.db import models
    model = AvailabilityConstraint
    formfield_overrides = {
            models.TextField: {'widget': forms.TextInput }
            }

class AvailabilityAdmin(admin.ModelAdmin):
    inlines = [AvailabilityConstraintInline]
admin.site.register(Availability, AvailabilityAdmin)

class SellerRateChartAdmin(admin.ModelAdmin):
    list_per_page = 10
    #list_select_related = ('seller','product')
    search_fields = ['seller__name','product__title','sku']
    list_display = ('sku','seller','product','list_price','offer_price', 'cashback_amount')
    list_filter = ('seller__client','product__status','seller')
admin.site.register(SellerRateChart, SellerRateChartAdmin)

class ShippingInfoAdmin(admin.ModelAdmin):
    pass
admin.site.register(ShippingInfo, ShippingInfoAdmin)

class ProductTagsAdmin(admin.ModelAdmin):
    list_per_page = 100
    list_display = ('tag','product','type','tab', 'sort_order')
    list_filter = ('type', 'tab')
    raw_id_fields = ('product',)
admin.site.register(ProductTags, ProductTagsAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ('tag','display_name',)
    list_filter = ('display_name',)
admin.site.register(Tag, TagAdmin)
