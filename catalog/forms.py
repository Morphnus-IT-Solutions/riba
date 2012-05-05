from django import forms
from categories.models import Feature
import re
from catalog.models import *
import logging
from django.forms.models import inlineformset_factory,modelformset_factory
import utils

log = logging.getLogger('request')

class ProductFeaturesForm(forms.ModelForm):
    class Meta:
        model = ProductFeatures
        exclude = ('type','feature')
    feature_type = forms.ChoiceField(choices=(
        ('fixed','Fixed'),
        ('variable','Variable')))
    #feature = forms.ModelChoiceField(queryset=Feature.objects.get_query_set(),widget=forms.Select(attrs={'onchange':"alert('hi');"}))

productFeatureFormSet = inlineformset_factory(Product,ProductFeatures, can_delete=False,extra=1)
productImageFormSet = inlineformset_factory(Product,ProductImage,can_delete=False,extra=2)
productSellerFormSet = inlineformset_factory(Product,SellerRateChart, can_delete=False,extra=1)
productShippingFormSet = inlineformset_factory(Product,ShippingInfo, can_delete=False,extra=1)
productVariantFormSet = inlineformset_factory(Product,ProductVariant,can_delete=False,extra=1,fk_name='blueprint')

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ('old_id','view_count','cart_count','pending_order_count','confirmed_order_count','category')

    category = forms.ModelChoiceField(queryset=Category.objects.get_query_set(),widget=forms.Select(attrs={'onchange':"alert('hi');"}))




class ProductImage(forms.Form):
    image = forms.ImageField()
    name = forms.CharField(max_length=25)

