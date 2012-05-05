from django import forms
from categories.models import Feature, Category, Store
import re
from catalog.models import *
from orders.models import *
from locations.models import *
from accounts.models import Account
import logging
from django.forms.models import inlineformset_factory,modelformset_factory
from utils.solrutils import *
from utils import utils
from django.db.models import Q

log = logging.getLogger('request')
search_log = logging.getLogger('search')

class SearchForm(forms.Form):
    q = forms.CharField(max_length=300, required=False)
    store = forms.ModelChoiceField(required=False,
                queryset = Store.objects.get_query_set(), empty_label="All Departments")
    request = None

    def __init__(self, request, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        sku_regex = re.compile(r'^sku:')
        store = self.cleaned_data.get('store',None)
        if store:
            categories = Category.objects.filter(store=store)
            category_query = (" OR ").join(str(x.id) for x in categories)
        else:
            category_query = ''
        q = self.cleaned_data.get('q','')
        q = str(q.encode('ascii','ignore')).strip()
        original_q = q
        q = utils.remove_special_chars(q)
        if sku_regex.match(q):
            q = ''
        if category_query and q:
            if q.isdigit():
                q = 'category_id:(%s)' % (category_query)
            else:
                q = '%s AND category_id:(%s)' % (q, category_query)
        if category_query and not q:
            q = 'category_id: (%s)' % category_query
        if not q:
            q = 'category_id: [* TO *]'
        if sku_regex.match(original_q):
            q = ' currency:inr'
        else:
            q = '%s AND currency:inr' % q
        q += ' AND client_id: %s' % self.request.client.client.id

        if sku_regex.match(original_q):
            sku = original_q.replace("sku:","")
            if sku:
                q += ' AND sku:%s' % sku
        self.cleaned_data['query'] = q
        return self.cleaned_data

class SortForm(forms.Form):
    def __init__(self, *args, **kw):
        super(SortForm, self).__init__(*args, **kw)
        self.fields['sort'] = forms.CharField(max_length=30, required=False, widget=forms.HiddenInput)

class FilterForm(forms.Form):
    request = None
    def __init__(self, request, inits, *args, **kw):
        self.request = request
        super(FilterForm, self).__init__(*args, **kw)
        # hidden fields for persisting data from header search
        self.fields['q'] = forms.CharField(widget=forms.HiddenInput, max_length=300, required=False)
        self.fields['store'] = forms.ModelChoiceField(widget=forms.HiddenInput, required=False,
                queryset = Store.objects.get_query_set())

        self.category = inits.get('category', None)
        self.brand = inits.get('brand', None)
        self.query = inits.get('query', None)
        self.tags = inits.get('tags', None)
        self.tag_ids = inits.get('tag_ids', None)
        self.tab = inits.get('tab', None)
        self.product = inits.get('product', None)
        self.price = inits.get('price', None)
        self.discount = inits.get('discount', None)
        self.clearance_sale = inits.get('clearance_sale', False)
        ignored_chars = '^(){{}};<>?/\|+'
        if self.query:
            for char in ignored_chars:
                self.query = self.query.replace(char, '')
        if self.category:
            self.query = 'category_id: %s' % self.category.id
        if self.brand:
            self.query = 'brand_id: %s' % self.brand.id
        if self.tags:
            self.query = 'tags: %s' % self.tags
        if self.tag_ids:
            self.query = 'tag_id: %s' % self.tag_ids
        if self.tab:
            self.query = 'tab_id: %s' % self.tab
        if not self.query:
            self.query = 'category_id: [* TO *]'
        if self.product:
            self.query = 'id: %s' % self.product
        if inits.get('q',''):
            self.fields['q'].initial = inits['q']
        if inits.get('store',''):
            self.fields['store'].initial = inits['store']

        # params to hold the request made to solr
        self.price_label = "offerprice_%s" % self.request.client.id
        self.discount_label = "discount_%s" % self.request.client.id
        params = {}
        if self.price:             
            params['fq'] = '%s:[%s TO %s], category_id:[* TO *], brand_id:[* TO *]' % (self.price_label, self.price['min'], self.price['max'])

        if self.discount:             
            params['fq'] = '%s:[%s TO %s], category_id:[* TO *], brand_id:[* TO *]' % (self.discount_label, self.discount['min'], self.discount['max'])
        facet_fields = []
        facet_queries = []
        facet_stats = []

        format_tag_ids = None
        
        if utils.is_future_ecom(self.request.client.client):
            # Add tag_id for FutureBazaar to fetch retailer tags
            facet_fields.append('tag_id')
            retailer_prod_tags = ProductTags.objects.select_related("tag__id").filter(type="retailers").values("tag__id").distinct()
            format_tag_ids = [tag["tag__id"] for tag in retailer_prod_tags]

        if self.clearance_sale:
            format_tag_ids = self.clearance_sale['format_tag_ids']
            solr_tag_ids = (" OR ").join(str(x) for x in format_tag_ids)
            if solr_tag_ids:
                params['fq'] = 'category_id:[* TO *], brand_id:[* TO *],  tag_id:(%s)' % (solr_tag_ids)
            # Add tag_id to facet fields for Clearance Sale
            # Check if Clearance is filtered by tag or category wise
            if self.clearance_sale['filter_id']:
                self.query += " AND %s_id:%s " % (self.clearance_sale['filter'], self.clearance_sale['filter_id'])
        # always facet by brand and category
        facet_fields.append('brand_id')
        facet_fields.append('category_id')

        facet_stats_name_map = {}
        # Get category filters and add them to facets
        if self.category:
            filters = self.category.filter_set.select_related('feature').all()
            for filter in filters:
                if filter.type == 'positive_presence':
                    # An and checkbox/positive presence is a filter on presence 
                    # of a feature and is applied on feature groups.
                    # e.g Connectivity has options of GPRS, Wi-Fi, Bluetooth.
                    # Each is a feature and has additional data 
                    # like 802.11 a/b/g/n. But we are interested in 
                    # having that feature, not the details.
                    facet_fields.append('%s_pr_l' % filter.feature_group.id)
                elif filter.type == 'buckets':
                    for filterbucket in filter.filterbucket_set.all():
                        facet_queries.append(filterbucket.get_facet_query())
                elif filter.type == 'slider':
                    facet_stats.append(filter.feature.solr_key())
                    facet_stats_name_map[filter.feature.solr_key()] = filter.name
                else:
                    facet_fields.append(filter.feature.solr_key())

                    
        if facet_fields:
            params['facet'] = 'true'
            params['facet_field'] = facet_fields
            params['facet_limit'] = '-1' # Fetching all facet counts
            params['facet_mincount'] = '1' # Ensure there are documents
        if facet_queries:
            params['facet_query'] = facet_queries

        # add params to get price info
        params['stats'] = 'true'
        params['stats_field'] = (self.price_label, self.discount_label)
        params['stats_field'] += tuple([x for x in facet_stats])

        if not utils.is_cc(self.request):
            self.query = '%s AND currency:inr' % self.query
        self.query += ' AND client_id: %s' % self.request.client.client.id

        if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
            self.query += ' AND -type:variant '
        if utils.is_holii_client(request.client.client) or utils.is_wholii_client(request.client.client):
            self.query += ' AND -type:variable '
        requested_category_id = request.GET.get('c',None)            
        if requested_category_id:
            self.query += " AND category_id:%s" % (requested_category_id)
        solr_result = solr_search(self.query, fields='id',
                highlight=None, score=False,
                sort=None, sort_order="asc", request=request, **params)
        facet_counts = solr_result.facet_counts
        if params['facet'] == 'true':
            if self.category:
                #filters = self.category.product_type.filter_set.select_related('feature').all()
                #filters = Filter.objects.select_related('feature').filter(product_type__type='mobile')
                for filter in filters:
                    choices = []
                    feature_choices = None
                    if filter.feature:
                        feature_choices = filter.feature.featurechoice_set.all()
                    if filter.feature_group:
                        id_feature_map = {}
                        key = '%s_pr_l' % filter.feature_group.id
                        key_facet_info = facet_counts['facet_fields'][key]
                        for feature in filter.feature_group.feature_set.all():
                            id_feature_map[str(feature.id)] = feature.name

                        for data, count in key_facet_info.items():
                            if count == 0:
                                continue
                            name = '%s (%s)' % (id_feature_map[str(data)], count)
                            choices.append((data, name))
                    elif filter.type == 'buckets':
                        key = '_fb%s_' % (filter.id)
                        fq_map = dict([(str(fb.get_facet_query()), fb) for fb in filter.filterbucket_set.all()])
                        choice_map = {}
                        for facet_query, count in facet_counts.get('facet_queries',{}).items():
                            if count == 0:
                                continue
                            if str(facet_query) in fq_map:
                                choice_map[fq_map[facet_query].id] = ('fb_%s' % fq_map[facet_query].id,
                                    '%s (%s)' % (fq_map[facet_query].display_name, count))

                        for fb in filter.filterbucket_set.all().order_by('sort_order'):
                            if fb.id in choice_map:
                                choices.append(choice_map[fb.id])

                    elif feature_choices:
                        key = filter.feature.solr_key()
                        for choice in feature_choices:
                            if choice.name in facet_counts['facet_fields'][key]:
                                choice_count = facet_counts['facet_fields'][key].get(choice.name,0)
                                if choice_count == 0:
                                    continue
                                choices.append((choice.name,
                                    '%s (%s)' % (choice.name, choice_count)))
                    elif filter.type != 'slider':
                        key = filter.feature.solr_key()
                        key_facet_info = facet_counts['facet_fields'][key]
                        for data, count in key_facet_info.items():
                            if count == 0:
                                continue
                            name = '%s (%s)' % (data, count)
                            if filter.feature.type == 'number':
                                name = '%s %s (%s)' % (("%.1f" % Decimal(data)).replace('.0',''), filter.feature.unit.code, count)
                            choices.append((data, name))
                    if filter.type != 'buckets':
                        choices = sorted(choices, key=lambda c:c[1].lower())
                    if filter.type != 'slider':
                        self.fields[key] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                            choices = tuple(choices),
                            required=False, label=filter.name)
                        self.fields[key].__setattr__('id',self.fields[key].label.lower().replace(' ','_'))

            if self.clearance_sale or utils.is_future_ecom(request.client.client):
                tag_inits = []
                tag_map = {}
                tags = Tag.objects.filter(id__in = facet_counts['facet_fields']['tag_id'])
                tags = tags.filter(id__in=format_tag_ids)
                for tag in tags:
                    tag_map[str(tag.id)] = tag
                choices = []
                custom_tag_id = None
                if self.clearance_sale and self.clearance_sale['filter'] == 'tag':
                    custom_tag_id = self.clearance_sale['filter_id'] 
                tag_facets = facet_counts['facet_fields']['tag_id'].items()
                tag_facets = sorted(tag_facets, key=lambda (k,v): (v,k))
                tag_facets.reverse()
                for data, count in tag_facets:
                    if int(data) not in format_tag_ids:
                        continue
                    if count == 0:
                        break
                    if custom_tag_id:
                        if custom_tag_id == tag_map[str(data)].id:
                            tag_inits.append(tag_map[str(data)].id)
                    else:
                        tag_inits.append(tag_map[str(data)].id)
                    name = '%s (%s)' % (tag_map[str(data)].display_name, count)
                    choices.append((tag_map[str(data)].id, name))
                choices = sorted(choices, key=lambda c:c[1].lower())
                self.fields['t'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                    choices = tuple(choices),
                    #initial = tag_inits,
                    required=False, label='Retailer')
            cat_inits = []
            cat_ids = []
            if requested_category_id:
                try:
                    requested_category = Category.objects.get(id=requested_category_id)
                except:
                    requested_category = None
            parent_category = None
            category_hierarchy = []
            custom_cat_id = None
            if self.clearance_sale:
                custom_cat_id = self.clearance_sale['filter_id'] if self.clearance_sale['filter'] == 'category' else None
                if custom_cat_id:
                    requested_category_id = custom_cat_id
                    requested_category = Category.objects.get(id=requested_category_id)
                    request.GET.c = custom_cat_id
            if not self.category:
                if requested_category_id:
                    category_hierarchy = utils.get_category_hierarchy(requested_category)
                    cat_ids = get_filter_category_ids(requested_category)
                else:
                    solr_cat_ids = facet_counts['facet_fields']['category_id']
                    parent_cats = CategoryGraph.objects.select_related(
                        "category").filter(Q(parent=None) & Q(category__id__in=solr_cat_ids))
                    cat_ids = [c.category.id for c in parent_cats]
            else:
                cat_ids = get_filter_category_ids(self.category)
                category_hierarchy = utils.get_category_hierarchy(self.category)
            categories = Category.objects.select_related('client').filter(
                id__in = facet_counts['facet_fields']['category_id'])
            category_map = {}
            choices = []
            for cat in categories:
                category_map[str(cat.id)] = cat
            category_facets = facet_counts['facet_fields']['category_id'].items() 
            if self.category and utils.is_leaf_category(self.category):
                parent_category = CategoryGraph.objects.filter(category=self.category).exclude(parent=None)
                if parent_category:
                    parent_category = parent_category[0]
                    category_facets = level_categories_facets(self.request, parent_category)
            category_facets = sorted(category_facets, key=lambda (k,v): (v,k))
            category_facets.reverse()
            category_dict_facets = {}
            for id, count in category_facets:
                if count == 0:
                    break
                category_dict_facets[id] = count
            categories = Category.objects.select_related("client").filter(id__in = category_dict_facets.keys())
            category_map = {}
            choices = []
            for cat in categories:
                category_map[str(cat.id)] = cat
            for data, count in category_dict_facets.iteritems():
                if str(data) not in category_map:
                    continue
                if category_map[str(data)].client != request.client.client:
                    continue
                if int(data)  in cat_ids:                
                    cat_inits.append(category_map[str(data)].id)
                name = '%s (%s)' % (category_map[str(data)].name, count)
                choices.append((category_map[str(data)].id, name))
            choices = sorted(choices, key=lambda c:c[1].lower())
            self.fields['c'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                    choices = tuple(choices),
                    initial = cat_inits,
                    required = False, label='Category')
            if category_hierarchy:
                self.fields['hc'] = forms.ChoiceField(widget=forms.Select,
                        choices = tuple(category_hierarchy),
                        initial = [],
                        required = False, label='Category Hierarchy')
            brand_inits = []
            brand_map = {}
            brand_facets = facet_counts['facet_fields']['brand_id'].items()
            brand_facets = sorted(brand_facets, key=lambda (k,v): (v,k))
            brand_facets.reverse()
            brand_dict_facets = {}
            for id, count in brand_facets:
                if count == 0:
                    break
                brand_dict_facets[id] = count
            brands = Brand.objects.select_related("id","name").filter(id__in = brand_dict_facets.keys())
            for brand in brands:
                brand_map[str(brand.id)] = brand
            choices = []
            for data, count in brand_dict_facets.iteritems():
                data = str(data)
                count = str(count)
                name = '%s (%s)' % (brand_map[data].name, count)
                choices.append((brand_map[data].id, name))
            choices = sorted(choices, key=lambda c:c[1].lower())
            self.fields['b'] = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                choices = tuple(choices),
                #initial = brand_inits,
                required=False, label='Brand')
            # price filter
            if solr_result:
                if solr_result.stats['stats_fields']['%s' % self.price_label]:
                    self.gmin = int(solr_result.stats['stats_fields']['%s' % self.price_label]['min'])
                    self.gmax = int(solr_result.stats['stats_fields']['%s' % self.price_label]['max'])
                    self.cmin = self.gmin
                    self.cmax = self.gmax
                    self.fields['min'] = forms.DecimalField(widget=forms.HiddenInput, required=False, label='Min. Price', initial=self.gmin)
                    self.fields['max'] = forms.DecimalField(widget=forms.HiddenInput,required=False, label='Max. Price', initial=self.gmax)
                if solr_result.stats['stats_fields']['%s' % self.discount_label]:
                    self.dmin = int(solr_result.stats['stats_fields']['%s' % self.discount_label]['min'])
                    self.dmax = int(solr_result.stats['stats_fields']['%s' % self.discount_label]['max'])
                    self.dlmin = self.dmin
                    self.dlmax = self.dmax
                    self.fields['min_discount'] = forms.CharField(widget=forms.HiddenInput, required=False, label='Min. Discount', initial=(self.dmin))
                    self.fields['max_discount'] = forms.CharField(widget=forms.HiddenInput, required=False, label='Max. Discount', initial=(self.dmax))
                for fs in facet_stats:
                    if solr_result.stats['stats_fields']['%s' % fs]:
                        setattr(self, 'gmin_'+fs, int(solr_result.stats['stats_fields']['%s' % fs]['min']))
                        setattr(self, 'gmax_'+fs, int(solr_result.stats['stats_fields']['%s' % fs]['max']))
                        setattr(self, 'cmin_'+fs, getattr(self, 'gmin_'+fs))
                        setattr(self, 'cmax_'+fs, getattr(self, 'gmax_'+fs))
                        self.fields['min_'+fs] = forms.CharField(widget=forms.HiddenInput(attrs={'class':'facet_slider'}), required=False,\
                                                 label=facet_stats_name_map[fs], initial=(getattr(self, 'gmin_'+fs)))
                        self.fields['min_'+fs].__setattr__('name', 'min_' + fs )
                        self.fields['min_'+fs].__setattr__('id', 'min_' + fs )
                        self.fields['max_'+fs] = forms.CharField(widget=forms.HiddenInput(attrs={'class':'hidden'}), required=False,\
                                                 label=facet_stats_name_map[fs], initial=(getattr(self, 'gmax_'+fs)))
                        self.fields['max_'+fs].__setattr__('name', 'max_' + fs)
                        self.fields['max_'+fs].__setattr__('id', 'max_' + fs)

    
    def clean(self):
        # other filters will be added as filter queries
        filter_queries = []
        facet_regex = re.compile('_f_[0-9]+_f')
        min_facet_regex = re.compile('min_f_[0-9]+_f')
        for key in self.cleaned_data.keys():
            if not self.cleaned_data[key]:
                # no filter selected from this set
                continue
            if min_facet_regex.match(key):
                facet_key = key.replace("min_", "")
                try:
                    if getattr(self, "gmin_" + facet_key) == self.cleaned_data['min_' + facet_key] and \
                       getattr(self, "gmax_" + facet_key) == self.cleaned_data['max_' + facet_key]:
                       pass
                    else:
                        setattr(self, "cmin_" + facet_key, self.cleaned_data['min_' + facet_key])
                        setattr(self, "cmax_" + facet_key, self.cleaned_data['max_' + facet_key])
                        facet_query = '%s:[%s TO %s]' % (facet_key, self.cleaned_data['min_' + facet_key], self.cleaned_data['max_' + facet_key])
                        filter_queries.append(facet_query)
                except KeyError:
                    pass
                continue
            if key in ['gmin','gmax','min','max','q','store','min_discount','max_discount', 'dmin', 'dmax'] or key.startswith('gf') or key.startswith('cf') or key.startswith('min_') or key.startswith('max_'):
                continue
            feature = None
            operator = " OR "
            if '_pr_' in key:
                operator = " AND "
            elif facet_regex.match(key):
                continue
            if not (key.endswith('_f') or key.endswith('_l')):
                skeys = ['"' + x + '"' for x in self.cleaned_data[key]]
            else:
                skeys = self.cleaned_data[key]
            fq = operator.join(skeys)
            if key == "c":
                key = "category_id"
            if key == "b":
                key = "brand_id"
            if key == "t":
                key = "tag_id"
            if key.endswith('_f') or key.endswith('_l') or key in ["brand_id", "category_id", "tag_id"]:
                fq = '%s:(%s)' % (key, fq)
            else:
                fq = '%s:%s' % (key, fq)
            if key.startswith('_fb'):
                try:
                    fbq = []
                    for key_value in self.cleaned_data[key]:
                        filterbucket = FilterBucket.objects.get(
                            pk=key_value.replace('_','').replace('fb',''))
                        fbq.append(filterbucket.get_facet_query())      
                    fq = ' OR '.join(fbq)
                    filter_queries.append(fq)
                except:
                    pass
                fq = None
            if fq:
                filter_queries.append(fq)
            log.info('Filter query is %s' % filter_queries) 
        price_query = None
        if not 'min' in self.cleaned_data or not 'max' in self.cleaned_data:
            price_query = None

        else:
            if self.cleaned_data['min'] and self.cleaned_data['max']:
                if self.gmin == self.cleaned_data['min'] and self.gmax == self.cleaned_data['max']:
                    price_query = None
                else:
                    self.cmin = self.cleaned_data['min']
                    self.cmax = self.cleaned_data['max']
                    price_query = '%s:[%s TO %s]' % (self.price_label, self.cleaned_data['min'], self.cleaned_data['max'])
            if price_query:
                filter_queries.append(price_query)

        discount_query = None
        if not 'min_discount' in self.cleaned_data or not 'max_discount' in self.cleaned_data:
            discount_query = None
        else:
            if self.cleaned_data['min_discount'] and self.cleaned_data['max_discount']:
                if self.dmin == self.cleaned_data['min_discount'] and self.dmax == self.cleaned_data['max_discount']:
                    discount_query = None
                else:
                    self.dlmin = self.cleaned_data['min_discount']
                    self.dlmax = self.cleaned_data['max_discount']
                    discount_query = '%s:[%s TO %s]' % (self.discount_label, self.cleaned_data['min_discount'], self.cleaned_data['max_discount'])
            if discount_query:
                filter_queries.append(discount_query)
        
        self.cleaned_data['filter_queries'] = filter_queries

        return self.cleaned_data

class FileUploadForm(forms.Form):
    status_file = forms.FileField()

def get_filter_category_ids(category):
    children_cats = CategoryGraph.objects.select_related("id").filter(parent__id=category.id)
    if not children_cats:
        parent_cat = CategoryGraph.objects.filter(category__id=category.id)
        if parent_cat:
            parent_cat = parent_cat[0]
            children_cats = CategoryGraph.objects.filter(parent=parent_cat.parent)
        parent_category = None
    cat_ids = [c.category_id for c in children_cats]
    return cat_ids
                
def level_categories_facets(request, parent_category):
    params = {}
    facet_fields = []
    facet_fields.append('category_id')
    params['facet'] = 'true'
    params['facet_field'] = facet_fields
    q = 'category_id:%s AND currency:inr AND client_id: %s' % (parent_category.parent.id, request.client.client.id)
    if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
        q += ' AND -type:variant '
    if utils.is_holii_client(request.client.client) or utils.is_wholii_client(request.client.client):
        q += ' AND -type:variable '
    solr_result = solr_search(q, fields='id', highlight=None, score=False, sort=None, request=request, sort_order="asc", **params)
    facet_counts = solr_result.facet_counts
    category_facets = facet_counts['facet_fields']['category_id'].items() 
    return category_facets

def get_facets_by_filter(request, query, facet_filter, **kwargs):
    params = {}
    fq = kwargs.get('fq', None)
    if fq:
        params['fq'] = fq
    facet_fields = []
    for filter in facet_filter:
        facet_fields.append(filter)
    params['facet'] = 'true'
    params['facet_field'] = facet_fields
    q = '%s AND currency:inr AND client_id: %s' % (query, request.client.client.id)
    if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
        q += ' AND -type:variant '
    if utils.is_holii_client(request.client.client) or utils.is_wholii_client(request.client.client):
        q += ' AND -type:variable '
    solr_result = solr_search(q, fields='id', highlight=None, score=False, sort=None, request=request, sort_order="", **params)
    facet_counts = solr_result.facet_counts
    facet_choices = {}
    for filter in facet_filter:
        try:
            facets = facet_counts['facet_fields'][filter].items()
        except KeyError:
            continue
        facets = sorted(facets, key=lambda (k,v): (v,k))
        facets.reverse()
        choices = []
        for data, count in facets:
            if count == 0:
                break
            choices.append((data, count))
        facet_choices[filter] = choices
    return facet_choices
