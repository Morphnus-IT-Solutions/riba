from django import forms
from categories.models import Feature, Category, Store
import re
from catalog.models import *
from orders.models import *
from reviews.models import *
from locations.models import *
import logging
from django.forms.models import inlineformset_factory,modelformset_factory
from utils import fields 
from feedback.models import ContactUs
from django.forms import ModelForm, Textarea
log = logging.getLogger('request')

class SearchForm(forms.Form):
    def __init__(self, *args, **kw):
        if kw.has_key('placeholder'):
            placeholder = kw.pop('placeholder')
        else:
            placeholder = 'e.g. Mobiles, Sony Camera, Bare Jeans'

        super(SearchForm, self).__init__(*args, **kw)
        self.fields['q'] = forms.CharField(max_length=300, required=False,
                widget = forms.TextInput(
                    attrs={
                        'autocomplete':'off',
                        'placeholder': placeholder,
                        }
                    ),
                initial = 'Search for deals'
                )
        self.fields['store'] = forms.ModelChoiceField(required=False,
                queryset = Store.objects.get_query_set(), empty_label="All Departments")
        self.fields['category'] = forms.ModelChoiceField(required=False,
                queryset = Category.objects.get_query_set())

    def clean(self):
        store = self.cleaned_data.get('store',None)
        category = self.cleaned_data.get('category',None)
        if not category:
            categories = Category.objects.filter(store=store)
            category_query = (" OR ").join(str(x.id) for x in categories)
        else:
            category_query = category.id
        q = self.cleaned_data.get('q','')
        self.cleaned_data['query'] = q
        if store:
            if not q:
                self.cleaned_data['query'] = 'category_id:(%s)' % (category_query)
            else:
                self.cleaned_data['query'] += ' AND category_id:(%s)' % (category_query)
        return self.cleaned_data

class CategoryForm(forms.Form):
    def __init__(self, *args, **kw):
        super(CategoryForm, self).__init__(*args, **kw)
        self.fields['q'] = forms.CharField(widget=forms.HiddenInput, max_length=300, required=False)
        self.fields['store'] = forms.ModelChoiceField(widget=forms.HiddenInput, required=False,
                queryset = Store.objects.get_query_set())
        self.fields['category'] = forms.ModelChoiceField(widget=forms.HiddenInput, required=False,
                queryset = Category.objects.get_query_set())

class SearchFilterForm(forms.Form):
    def __init__(self,q, *args, **kw):
        self.q = q
        super(SearchFilterForm, self).__init__(*args, **kw)

        facet_fields, facet_queries = [], []
        facet_fields.append('category_id')
        facet_fields.append('brand_exact')
        params = {}
        if facet_fields:
            params['facet'] = 'true'
            params['facet_field'] = facet_fields
        if facet_queries:
            params['facet'] = 'true'
            params['facet_query'] = facet_queries

        # add params to get price info
        params['stats'] = 'true'
        params['stats_field'] = 'price'
        if not q:
            q = '*:*'
        q += ' AND type:(variant OR normal)'
        solr_result = solr_search(q, fields='id',
                highlight=None, score=False,
                sort=None, sort_order="asc", **params)
        facet_counts = solr_result.facet_counts
        if params['facet'] == 'true':
            # category filter
            choices = []
            cids = facet_counts['facet_fields']['category_id']
            categories = Category.objects.filter(pk__in=cids)
            cat_map = {}
            for category in categories:
                cat_map[category.id] = category.name

            cat_inits = []
            for x, count in facet_counts['facet_fields']['category_id'].items():
                if count !=0:
                    cat_inits.append(x)
            for data, count in facet_counts['facet_fields']['category_id'].items():
                if count == 0:
                    continue
                name = '%s (%s)' % (cat_map[int(data)], count)
                choices.append((data, name))
            self.fields['category_id'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                choices = tuple(choices),
                initial = cat_inits,
                required=False, label='Category')

            brand_inits = []
            brand_names = facet_counts['facet_fields']['brand_exact']
            brands = Brand.objects.filter(name__in = brand_names)
            brand_map = {}
            for brand in brands:
                brand_map[brand.name] = brand.id
            for x,count in facet_counts['facet_fields']['brand_exact'].items():
                if count !=0:
                    brand_inits.append(brand_map[x])
            # brand filter
            choices = []
            for data, count in facet_counts['facet_fields']['brand_exact'].items():
                if count == 0:
                    continue
                name = '%s (%s)' % (data, count)
                choices.append((brand_map[data], name))
            self.fields['b'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                choices = tuple(choices),
                initial = brand_inits,
                required=False, label='Brand')


            # price filter
            if solr_result:
                if solr_result.stats['stats_fields']['price']:
                    self.gmin = solr_result.stats['stats_fields']['price']['min']
                    self.gmax = solr_result.stats['stats_fields']['price']['max']
                    self.cmin = self.gmin
                    self.cmax = self.gmax
                    self.fields['min'] = forms.DecimalField(widget=forms.HiddenInput, required=True, label='Min. Price', initial=self.gmin)
                    self.fields['max'] = forms.DecimalField(widget=forms.HiddenInput,required=True, label='Max. Price', initial=self.gmax)



    def clean(self):

        # other filters will be added as filter queries
        filter_queries = []
        for key in self.cleaned_data.keys():
            if not self.cleaned_data[key]:
                # no filter selected from this set
                continue
            if key in ['gmin','gmax','min','max']:
                continue
            feature = None
            operator = " OR "
            if not key.endswith('_f'):
                if key == 'b':
                    brand_ids = self.cleaned_data[key]
                    brands = Brand.objects.filter(id__in = brand_ids)
                    brand_names = []
                    for brand in brands:
                        brand_names.append(brand.name)
                    skeys = ['"' + x + '"' for x in brand_names]
                else:
                    skeys = ['"' + x + '"' for x in self.cleaned_data[key]]
            else:
                skeys = self.cleaned_data[key]
            fq = operator.join(skeys)
            if key.endswith('_f'):
                fq = '%s:(%s)' % (key, fq)
            elif key == 'b':
                fq = '%s:(%s)' % ('brand_exact',fq)
            else:
                fq = '%s:%s' % (key, fq)
            filter_queries.append(fq)
        if 'min' in self.cleaned_data and 'max' in self.cleaned_data:
            if self.cleaned_data['min'] and self.cleaned_data['max']:
                if self.gmin == self.cleaned_data['min'] and self.gmax == self.cleaned_data['max']:
                    price_query = None
                else:
                    self.cmin = self.cleaned_data['min']
                    self.cmax = self.cleaned_data['max']
                    price_query = '%s:[%s TO %s]' % ('price', self.cleaned_data['min'], self.cleaned_data['max'])

                if price_query:
                    filter_queries.append(price_query)
        self.cleaned_data['filter_queries'] = filter_queries
        return self.cleaned_data


class CategoryFilterForm(forms.Form):
    def __init__(self, category,q, *args, **kw):
        self.category = category
        self.q = q
        #self.store = ''
        super(CategoryFilterForm, self).__init__(*args, **kw)

        if category:
            #self.store = category.store
            facet_fields, facet_queries = [], []
            facet_fields.append('brand_exact')
            filters = category.filter_set.select_related('feature').all()
            for filter in filters:
                key = filter.feature.solr_key()
                facet_fields.append( key)
            params = {}
            if facet_fields:
                params['facet'] = 'true'
                params['facet_field'] = facet_fields
            if facet_queries:
                params['facet'] = 'true'
                params['facet_query'] = facet_queries
            # add params to get price info
            params['stats'] = 'true'
            params['stats_field'] = 'price'
            if q:
                query =  q
            else:
                query = 'category_id:%s' % category.id
            query += ' AND type:(normal OR variant)'
            solr_result = solr_search(query, fields='id',
                    highlight=None, score=False,
                    sort=None, sort_order="asc", **params)
            facet_counts = solr_result.facet_counts
            if params['facet'] == 'true':
                for filter in filters:
                    key = filter.feature.solr_key()
                    choices = []
                    feature_choices = filter.feature.featurechoice_set.all()
                    if feature_choices:
                        for choice in feature_choices:
                            if choice.name in facet_counts['facet_fields'][key]:
                                choice_count = facet_counts['facet_fields'][key].get(choice.name,0)
                                choices.append((choice.name,
                                    '%s (%s)' % (choice.name, choice_count)))
                    else:
                        key_facet_info = facet_counts['facet_fields'][key]
                        for data, count in key_facet_info.items():
                            name = '%s (%s)' % (data, count)
                            if filter.feature.type == 'number':
                                name = '%s %s (%s)' % (data, filter.feature.unit.code, count)
                            choices.append((data, name))
                    self.fields[key] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                        choices = tuple(choices),
                        required=False, label=filter.feature.name)

                brand_inits = []
                brand_map = {}
                brand_names = facet_counts['facet_fields']['brand_exact']
                brands = Brand.objects.filter(name__in = brand_names)
                for brand in brands:
                    brand_map[brand.name] = brand.id
                for x,count in facet_counts['facet_fields']['brand_exact'].items():
                    if count !=0:
                        brand_inits.append(brand_map[x])
                # brand filter
                choices = []
                for data, count in facet_counts['facet_fields']['brand_exact'].items():
                    if count == 0:
                        continue
                    name = '%s (%s)' % (data, count)
                    choices.append((brand_map[data], name))
                self.fields['b'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                    choices = tuple(choices),
                    initial = brand_inits,
                    required=False, label='Brand')

                # price filter
                if solr_result:
                    self.gmin = solr_result.stats['stats_fields']['price']['min']
                    self.gmax = solr_result.stats['stats_fields']['price']['max']
                    self.cmin = self.gmin
                    self.cmax = self.gmax
                    self.fields['min'] = forms.DecimalField(widget=forms.HiddenInput, required=False, label='Min. Price', initial=self.gmin)
                    self.fields['max'] = forms.DecimalField(widget=forms.HiddenInput,required=False, label='Max. Price', initial=self.gmax)

    def clean(self):
        category = self.category

        # other filters will be added as filter queries
        filter_queries = []
        for key in self.cleaned_data.keys():
            if not self.cleaned_data[key]:
                # no filter selected from this set
                continue
            if key in ['gmin','gmax','min','max']:
                continue
            feature = None
            operator = " OR "
            if not key.endswith('_f'):
                skeys = ['"' + x + '"' for x in self.cleaned_data[key]]
            else:
                skeys = self.cleaned_data[key]
            fq = operator.join(skeys)
            if key.endswith('_f'):
                fq = '%s:(%s)' % (key, fq)
            else:
                fq = '%s:%s' % (key, fq)
            filter_queries.append(fq)
        if self.cleaned_data['min'] and self.cleaned_data['max']:
            if self.gmin == self.cleaned_data['min'] and self.gmax == self.cleaned_data['max']:
                price_query = None
            else:
                self.cmin = self.cleaned_data['min']
                self.cmax = self.cleaned_data['max']
                price_query = '%s:[%s TO %s]' % ('price', self.cleaned_data['min'], self.cleaned_data['max'])

            if price_query:
                filter_queries.append(price_query)
        self.cleaned_data['filter_queries'] = filter_queries
        brand_ids = self.cleaned_data['b']
        brands = Brand.objects.filter(id__in = brand_ids)
        brand_names = []
        for brand in brands:
            brand_names.append(brand.name)
        del self.cleaned_data['b']
        self.cleaned_data['brand_exact'] = brand_names
        return self.cleaned_data


class BrandFilterForm(forms.Form):
    def __init__(self, brand,*args, **kw):
        super(BrandFilterForm, self).__init__(*args, **kw)
        self.brand = brand
        facet_fields, facet_queries = [], []
        facet_fields.append('category_id')
        params = {}
        if facet_fields:
            params['facet'] = 'true'
            params['facet_field'] = facet_fields
        if facet_queries:
            params['facet'] = 'true'
            params['facet_query'] = facet_queries

        # add params to get price info
        params['stats'] = 'true'
        params['stats_field'] = 'price'
        solr_result = solr_search('brand:' + brand, fields='id',
                highlight=None, score=False,
                sort=None, sort_order="asc", **params)

        facet_counts = solr_result.facet_counts
        if params['facet'] == 'true':
            # category filter
            choices = []
            cids = facet_counts['facet_fields']['category_id']
            categories = Category.objects.filter(pk__in=cids)
            cat_map = {}
            for category in categories:
                cat_map[category.id] = category.name

            cat_inits = []
            for x, count in facet_counts['facet_fields']['category_id'].items():
                if count !=0:
                    cat_inits.append(x)
            for data, count in facet_counts['facet_fields']['category_id'].items():
                if count == 0:
                    continue
                name = '%s (%s)' % (cat_map[int(data)], count)
                choices.append((data, name))
            self.fields['category_id'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                choices = tuple(choices),
                initial = cat_inits,
                required=False, label='Category')

            if solr_result:
                if solr_result.stats['stats_fields']['price']:
                    self.gmin = solr_result.stats['stats_fields']['price']['min']
                    self.gmax = solr_result.stats['stats_fields']['price']['max']
                    self.cmin = self.gmin
                    self.cmax = self.gmax
                    self.fields['min'] = forms.DecimalField(widget=forms.HiddenInput, required=True, label='Min. Price', initial=self.gmin)
                    self.fields['max'] = forms.DecimalField(widget=forms.HiddenInput,required=True, label='Max. Price', initial=self.gmax)


    def clean(self):

        # other filters will be added as filter queries
        filter_queries = []
        for key in self.cleaned_data.keys():
            if not self.cleaned_data[key]:
                # no filter selected from this set
                continue
            if key in ['gmin','gmax','min','max']:
                continue
            feature = None
            operator = " OR "
            fq = operator.join(self.cleaned_data[key])
            fq = '%s:(%s)' % (key, fq)
            filter_queries.append(fq)
        self.cleaned_data['filter_queries'] = filter_queries
        return self.cleaned_data


class DeliveryInfoForm(forms.ModelForm):
    class Meta:
        model = DeliveryInfo
        exclude = ('notes',)

class GiftInfoForm(forms.ModelForm):
    class Meta:
        model = GiftInfo
        exclude = ('order',)

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        exclude = ('type','profile','account','uses')

class FBRegisterForm(forms.Form):
    name = forms.CharField(max_length = 50, required=False)
    email = forms.EmailField(required=True, error_messages={
        'required': 'Please enter email id',
        'invalid': 'Please enter a valid email id'})
    mobile = forms.CharField(max_length=10,required=True,validators=[fields.validate_phone],
                error_messages={
                    'required': 'Please enter your mobile number',
                    'invalid': 'Please enter a valid 10 digit mobile number',
                    }
            )

class DealRegisterForm(forms.Form):
    name = forms.CharField(max_length = 50, required=False)
    email = forms.EmailField(required=True, error_messages={
        'required': 'Please enter email id',
        'invalid': 'Please enter a valid email id'})
    mobile = forms.CharField(max_length=10,required=False,validators=[fields.validate_phone],
                error_messages={
                    'invalid': 'Please enter a valid 10 digit mobile number',
                    }
            )

class LogggedInFBForm(forms.Form):
    receive_email = forms.BooleanField(required = False)
    sms_alerts = forms.BooleanField(required = False)

class PhoneNoForm(forms.Form):
    mobile_no = forms.CharField()

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("title","review","rating")
#        widgets = {
#            'review' : forms.TextArea(attrs={'cols':40, 'rows':10}),
#        }
    title = forms.CharField(max_length=100)
    #review = forms.CharField(min_length=140,widget=forms.Textarea)

    def clean(self):
#        import pdb
#        data = self.cleaned_data
#        pdb.set_trace()
        error = ''
        if ("title" in self.cleaned_data and not self.cleaned_data["title"].strip()) or ("title" not in self.cleaned_data):
            error += u"Enter Review Title\n"
#            raise forms.ValidationError(u"Enter Review Title")
        if "review" in self.cleaned_data:
			if len(self.cleaned_data["review"]) < 140:
				error += u"Your Review is less than 140 characters long\n"
#                raise forms.ValidationError(u"Your Review is less than 140 characters in length")
        else:
            error += "Enter Your Review\n"
#            raise forms.ValidationError(u"Enter Your Review")
        if "rating" in self.cleaned_data and not self.cleaned_data["rating"] or ("rating" not in self.cleaned_data):
            error += u"Enter Your Rating\n"
#            raise forms.ValidationError(u"Enter Your Rating")
        if error :
#            print"error %s" %error
            raise forms.ValidationError(error)

        return self.cleaned_data

class WinRegisterForm(forms.Form):
    name = forms.CharField(max_length = 50, required=False)
    email = forms.EmailField(max_length=100, required=False, error_messages={
        'required': 'Enter email id',
        'invalid': 'Enter a valid email id'})
    mobile = forms.CharField(max_length=10,required=False,validators=[fields.validate_phone],
                error_messages={
                    'required': 'Enter your Mobile no.',
                    'invalid': 'Enter a valid 10 digit mobile no.',
                    }
            )

    scratch_code = forms.CharField(max_length = 10, required=True, error_messages={
        'required': 'Enter Valid Scratch Code',
        'invalid':'Enter Valid Scratch Code',})

class ContactUsForm(forms.ModelForm):
    class Meta:
        model = ContactUs
        fields = ('subject','first_name', 'last_name', 'email', 'phone', 'comments')

class DateForm(forms.Form):
    start_date = forms.DateField(required = False)#, input_formats = ['%Y-%m-%d'])
    end_date = forms.DateField(required = False)#, input_formats = ['%Y-%m-%d'])
    order_id = forms.CharField(required = False)

class PriceCompareForm(forms.Form):
    search_for = forms.CharField(max_length=300, required=True)
