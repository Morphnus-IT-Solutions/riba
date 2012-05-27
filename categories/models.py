from django.core.exceptions import ValidationError
from storage import upload_storage
from imagekit.models import ImageModel
import re
from accounts.models import Client
from django.db import models
from django.core.cache import cache
# Create your models here.

class Store(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def url(self):
        return "%s/st/%s/" % (self.slug,self.id)

    def __unicode__(self):
        return self.name

class CategoryQuerySet(models.query.QuerySet):

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
            obj = self.get_from_cache('categories:category:%s' % kwargs['id'])
            if obj:
                return obj
            else:
                obj = super(CategoryQuerySet, self).get(*args, **kwargs)
                self.set_in_cache('categories:category:%s' % obj.id, obj, 0)
                return obj

        if 'pk' in kwargs and kwargs.keys() == ['pk']:
            obj = self.get_from_cache('categories:category:%s' % kwargs['pk'])
            if obj:
                return obj
            else:
                obj = super(CategoryQuerySet, self).get(*args, **kwargs)
                self.set_in_cache('categories:category:%s' % obj.id, obj, 0)
                return obj
        return super(CategoryQuerySet, self).get(*args, **kwargs)


class CategoryCacheManager(models.Manager):
    use_for_related_fields = True

    def get_query_set(self):
        return CategoryQuerySet(self.model)

class Category(models.Model):
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('name',)

    name = models.CharField(max_length=50)
    #client = models.ForeignKey('accounts.Client')
    #tagline = models.CharField(max_length=500, blank = True, null = True)
    description = models.TextField(blank = True, null = True)
    slug = models.SlugField(max_length=100)

    image = models.ImageField(upload_to = 'category/%Y/%m', storage = upload_storage, blank = True, null = True)
    sort_order = models.PositiveIntegerField(default=1)
    #objects = CategoryCacheManager()

    def save(self, *args, **kwargs):
        if self.id:
            cache.delete('categories:category:%s' % self.id)
        return super(Category, self).save(*args, **kwargs)

    def featured_products(self):
        from promotions.models import FeaturedProducts
        products = FeaturedProducts.objects.filter(category=self,type='mega_drop_down')[:2]
        return products

    def url(self):
        return "%s/ch/%s/" % (self.slug,self.id)

    def get_children(self,category,children):
        try:
            graph = CategoryGraph.objects.filter(parent=category)
        except CategoryGraph.DoesNotExist:
            return children
        if not graph:
            return children
        for node in graph:
            children.append(node.category)
            self.get_children(node.category,children)
        return children

    def get_all_children(self):
        cat = self
        children = []
        children = self.get_children(cat,children)
        return children

    def get_parents(self,category,parents):
        g = CategoryGraph.objects.filter(category=category)

        for graph in g:
            parent = graph.parent
            if not parent:
                continue
            else:
                parents.append(parent)
                self.get_parents(parent,parents)
        return

    def get_all_parents(self):
        cat = self
        parents = []
        self.get_parents(cat,parents)
        exists = {}
        unique_parents = []
        for p in parents:
            if p.id not in exists:
                unique_parents.append(p)
                exists[p.id] = True
        return unique_parents


    def has_products(self):
        if self.product_set.filter(status='active').count() > 0:
            return True
        else:
            total = 0
            for c in self.get_all_children():
                total += c.product_set.filter(status='active').count()
            if total > 0:
                return True
            return False
        

    def __unicode__(self):
        return self.name
        #return '%s(%s)-%s' % (self.name, self.ext_id, self.client.name)


    def get_display_url(self):
        images = self.categoryimage_set.all().order_by('id')
        if images:
            display = images[0].get_display_url()
        else:
            display = ''
        return display


    def get_thumbnail_218x218(self):
        images = self.categoryimage_set.all().order_by('id')
        if images:
            thumb = images[0].get_thumbnail_218x218()
        else:
            thumb = ''
        return thumb

    def get_display_170x170(self):
        images = self.categoryimage_set.all().order_by('id')
        if images:
            disp = images[0].get_display_170x170()
        else:
            disp = ''
        return disp

    def get_thumbnail_110x110(self):
        images = self.categoryimage_set.all().order_by('id')
        if images:
            disp = images[0].get_thumbnail_110x110()
        else:
            disp = ''
        return disp

    def get_banner_670x342(self):
        images = self.categoryimage_set.all().order_by('-id')
        if images:
            banner = images[0].get_banner_670x342()
        else:
            banner = ''
        return banner


class CategoryImage(ImageModel):
    category = models.ForeignKey(Category)
    image = models.ImageField(upload_to='category/%Y/%m', storage=upload_storage,blank=True,null=True)
    name = models.CharField(max_length=25, blank = True, null = True)
    url = models.URLField(blank = True, null = True)

    class IKOptions:
        # This inner class is where we define the ImageKit options for the model
        spec_module = 'categories.specs'
        cache_dir = 'pc'
        image_field = 'image'

    def get_thumbnail_218x218(self):
        return self.thumbnail_218x218.url

    def get_thumbnail_110x110(self):
        return self.thumbnail_110x110.url

    def get_display_170x170(self):
        return self.display_170x170.url

    def get_display_url(self):
        return self.display.url

    def get_banner_670x342(self):
        return self.banner_670x342.url


class ProductType(models.Model):
    class Meta:
        unique_together = ('type', 'client')
    type = models.CharField(max_length=50)
    client = models.ForeignKey(Client, blank=True, null=True)
    def __unicode__(self):
        return '%s - %s' % (self.type, self.client)

class CategoryGraph(models.Model):
    category = models.ForeignKey(Category)
    parent = models.ForeignKey(Category, related_name='category_parent',blank=True,null=True)
    #position =  models.CharField(max_length=5,default='left',choices=(
    #    ('left','Left'),
    #    ('right','Right')))
    sort_order = models.PositiveIntegerField(default=1)

    def __unicode__(self):
        return "Parent: %s, Child: %s" % (self.parent.name, self.category.name)

class FilterGroup(models.Model):
    class Meta:
        unique_together = ('category', 'sort_order')

    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category)
    sort_order = models.PositiveIntegerField(default=1)

    def __unicode__(self):
        return self.name

class FeatureGroup(models.Model):
    class Meta:
        unique_together = ('product_type', 'name')

    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, blank=True, null=True)
    product_type = models.ForeignKey(ProductType, blank=True, null=True)

    hide_unavailable_features = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=1)

    def __unicode__(self):
        return '%s - %s -%s' % (self.name, self.category, self.product_type)

class Unit(models.Model):
    name = models.CharField(max_length=150, unique=True, db_index=True)
    code = models.CharField(max_length=150, unique=True, db_index=True)

    # if this unit is an extension of base unit
    base = models.ForeignKey('self', blank=True, null=True)
    multiplier = models.DecimalField(max_digits=12, decimal_places=2,
            blank=True, null=True,
            help_text='How many base units will result in one unit of this.')
    inverse_multipler = models.BooleanField(default=False, help_text=
            'Set this on if base unit is bigger than this unit. Multiplier will be used as denominator for conversion.')

    def __unicode__(self):
        return self.name

class Feature(models.Model):

    category = models.ForeignKey(Category, blank=True, null=True)
    product_type = models.ForeignKey(ProductType, blank=True, null=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=100, choices=(
        ('text', 'Text'),
        ('boolean','Boolean'),
        ('number','Number')))
    group = models.ForeignKey(FeatureGroup, null=True, blank=True)
    allow_multiple_select = models.BooleanField(default=False)
    unit = models.ForeignKey(Unit, blank=True, null=True)

    is_visible = models.BooleanField(default=True)
    min = models.DecimalField(blank=True, null=True,
            max_digits = 10, decimal_places=2,
            help_text='Enter minimum allowed value if type is number')
    max = models.DecimalField(blank=True, null=True,
            max_digits = 10, decimal_places=2,
            help_text='Enter maximum allowed value if type is number')
    sort_order = models.PositiveIntegerField(default=1)
    use_for_icons = models.BooleanField(default=False)
    use_as_key_features = models.BooleanField(default=False)
    index_for_presence = models.BooleanField(default=False)

    def clean(self):
        if self.min and self.max:
            if self.max < self.min:
                raise ValidationError("Minimum value should be less than maximum value")
        if self.group:
            if not self.group.product_type.id == self.product_type.id:
                raise ValidationError('%s does not belong to %s. Groups should belong to same product type as feature.' %
                (self.group.name, self.product_type.type))


    def __unicode__(self):
        if self.product_type:
            return '%s, %s' % (self.name, self.product_type)
        else:
            return '%s, %s' % (self.name, self.category)

    def solr_key(self):
        key = 'f_%s' % self.id
        if self.type == 'boolean':
            key = '%s_%s' % (key, 'b')
        if self.type == 'text':
            key = '%s_%s' % (key,'s')
        if self.type == 'number':
            key = '%s_%s' % (key, 'f')

        return key

class FeatureChoice(models.Model):
    class Meta:
        unique_together = ('name','feature')

    name = models.CharField(max_length=150)
    feature = models.ForeignKey(Feature)
    icon = models.ImageField(upload_to = 'features/%Y/%m', blank=True, null=True, storage=upload_storage)

    def __unicode__(self):
        return self.name

    def clean(self):
        if self.feature.type == 'number':
            try:
                f = float(self.name)
            except:
                raise ValidationError('Invalid choice for %s. %s is not a valid number' % (self.feature.name, self.name))
        if self.feature.type == 'boolean':
            raise ValidationError('Choices cannot be defined for boolean features')

class FilterBucket(models.Model):
    fil = models.ForeignKey('categories.Filter')
    sort_order = models.IntegerField(default=10)
    start = models.CharField(max_length=10, default='*')
    end = models.CharField(max_length=10, default='*')
    display_name = models.CharField(max_length=50, blank=True, null=True)

    def get_facet_query(self):
        return '%s: [%s TO %s]' % (self.fil.feature.solr_key(),
            self.start,
            self.end)

class Filter(models.Model):
    class Meta:
        unique_together = ('category','sort_order')

    category = models.ForeignKey(Category)
    name = models.CharField(max_length=100)
    feature = models.ForeignKey(Feature, blank=True, null=True)
    feature_group = models.ForeignKey(FeatureGroup, blank=True, null=True)

    type = models.CharField(max_length=50, choices=(
        ('slider','Slider'),
        ('checkbox','Checkbox'),
        ('positive_presence','Positive Presence'),
        ('buckets', 'Bucketed'),
        ('radio','Radio')))
    sort_order = models.PositiveIntegerField(default=1)

    def __unicode__(self):
        return 'Filter %s for %s' % (self.name, self.category)

    def solr_key(self):
        if self.feature_group:
            return self.feature_group.solr_key()
        return self.feature.solr_key()
    
class MegaDropDown(models.Model):
    client = models.ForeignKey('accounts.Client')
    display_name = models.CharField(max_length=100,blank=True)
    list = models.ForeignKey('lists.List',blank=True,null=True)
    category = models.ForeignKey(Category,blank=True,null=True)
    sort_order = models.PositiveIntegerField(default=1)
    type = models.CharField(max_length=30,default='category',choices=(
        ('category','Category'),
        ('menu_level2_category', 'Menu Level-2 Category'),
        ('list','List'),
        ('group_of_lists','Group of Lists')))
    level_2_type = models.CharField(max_length=30, choices=(
        ('grouped_category','Grouped Category'),
        ('only_retailers', 'Only Retailers')), blank=True, null=True)

class CategoryProducttypeMapping(models.Model):
    category = models.ForeignKey(Category)
    product_type = models.ForeignKey(ProductType)

    def __unicode__(self):
        return 'Category=%s, ProductType=%s' %(self.category, self.product_type)
