from django import forms
from django.forms.models import inlineformset_factory
from lists.models import List, ListItem
from datetime import datetime
from django.conf import settings
from django.forms.models import BaseModelFormSet
from utils import fields, utils
from django.forms.models import BaseInlineFormSet
from imagekit.models import ImageModel
from catalog.models import Product, ProductTags, Tag, SellerRateChart
from storage import upload_storage
from decimal import Decimal
from accounts.models import *
from users.models import *
from django.forms.models import modelformset_factory
from django.contrib.auth.models import Group
from users.models import Tab
from accounts.models import Account
from web.models import Coordinates

class AddUserForm(forms.Form):
    username = forms.CharField(label='User Name')
    role = forms.ModelChoiceField(queryset=Group.objects.filter(name__in=['Sellers Admin','Sellers Manager','Sellers User','Sellers Client','Sellers Agent','IFS']
))
    tabs = forms.ModelMultipleChoiceField(queryset=Tab.objects.all())
    accounts = forms.ModelMultipleChoiceField(queryset=Account.objects.all())

class ListsForm(forms.ModelForm):
	class Meta:
		model = List
		fields = ("title", "slug","client", "type", "template_type", "description", "starts_on", "ends_on", "banner_image", "redirect_to", "banner_type")
	#ItemFormSet = inlineformset_factory(List, ListItem, formset = BaseItemFormSet, extra = 3) 
	starts_on = forms.DateTimeField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Select a Date'}))
	ends_on=forms.DateTimeField(required=False , widget=forms.TextInput(attrs={'placeholder': 'Select a Date'}))


class ListItemForm(forms.ModelForm):
	class Meta:
		model = ListItem
		fields = ("id","sku", "sequence","user_description","user_title","user_features","status", "user_image", "redirect_to")
	sku = forms.ModelChoiceField(queryset=SellerRateChart.objects.all(), widget=forms.TextInput, label='Seller Rate Chart ID', required=False)
	sequence = forms.IntegerField(required=False, min_value=1, max_value=9999)
	status = forms.ChoiceField(required=False, choices=(
				('active', 'Active'),
				('in_queue', 'In Queue')))
	user_description = forms.CharField(label='Description', widget=forms.Textarea, required=False)
	user_title = forms.CharField (max_length=1000, label='Title', required=False)
	user_image = forms.ImageField(label='Image', required=False)
	user_features = forms.CharField(label='Features', widget=forms.Textarea, required=False)


class CoordinatesForm(forms.ModelForm):
	class Meta:
		model=Coordinates
		fields = ("id","list", "sequence", "co_ordinates", "link")
	sequence = forms.IntegerField(min_value=1, max_value=9, required=False)
	co_ordinates=forms.CharField(required=False)
	link=forms.CharField(required=False)

class BaseItemFormSet(BaseInlineFormSet):
	pass
