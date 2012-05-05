from django.contrib import admin
from categories.models import *
from django.db.models import *

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

class StoreAdmin(admin.ModelAdmin):
    search_fields = ['name']
admin.site.register(Store, StoreAdmin)

class FilterBucketInline(admin.TabularInline):
    model = FilterBucket
    extra = 1

class CategoryImageInline(admin.TabularInline):
    model = CategoryImage
    extra = 2

class CategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']
    inlines = [CategoryImageInline]
    list_display = ('name', 'slug', )
admin.site.register(Category, CategoryAdmin)


class CategoryImageAdmin(admin.ModelAdmin):
    pass
admin.site.register(CategoryImage, CategoryImageAdmin)


class CategoryGraphAdmin(admin.ModelAdmin):
    search_field = ['category']
    list_display = ('category','parent', 'sort_order')
admin.site.register(CategoryGraph, CategoryGraphAdmin)

class MegaDropDownAdmin(admin.ModelAdmin):
    search_field = ['category','list']
    list_display = ('category', 'client','type','sort_order','list', 'level_2_type')
    list_filter = ('type','client')
    raw_id_fields = ('category',)
admin.site.register(MegaDropDown, MegaDropDownAdmin)

class UnitAdmin(admin.ModelAdmin):
    search_fields = ['name','code']
    list_display = ('name','code','base','multiplier','inverse_multipler')
admin.site.register(Unit, UnitAdmin)

class FilterGroupAdmin(admin.ModelAdmin):
    pass
admin.site.register(FilterGroup, FilterGroupAdmin)

class FilterAdmin(admin.ModelAdmin):
    inlines = [FilterBucketInline]
    search_fields = ['name','feature__name']
    list_display = ('name', 'feature', 'sort_order')
    list_filter = ('category',)
admin.site.register(Filter, FilterAdmin)

class FeatureAdminInline(admin.TabularInline):
    model = Feature
    extra = 3

class FeatureGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'category','product_type','sort_order')
    list_filter = ('product_type',)
    inlines = [FeatureAdminInline]
admin.site.register(FeatureGroup, FeatureGroupAdmin)

class FeatureChoiceInline(admin.TabularInline):
    model = FeatureChoice
    extra = 5

class FeatureAdmin(admin.ModelAdmin):
    search_fields = ['name', 'category__name']
    list_display = ('name', 'category', 'product_type', 'type', 'group', 'unit', 'sort_order','allow_multiple_select')
    list_filter = ('type', 'product_type',)
    inlines = [FeatureChoiceInline]
admin.site.register(Feature, FeatureAdmin)

class FeatureChoiceAdmin(admin.ModelAdmin):
    search_fields = ['name','feature__name']
    list_display = ('name','feature')
    list_filter = ('feature',)
admin.site.register(FeatureChoice, FeatureChoiceAdmin)


class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('type',)
admin.site.register(ProductType, ProductTypeAdmin)
