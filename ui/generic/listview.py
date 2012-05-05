from django.db import models
from itertools import izip, islice

class ListView:
    SEARCH = 'lv.q'
    SORT = 'lv.sort'

    class ImproperlyConfigured(Exception):
        pass

    class InvalidInput(Exception):
        pass
    
    def __init__(self, model, col_headers=None, sorts_by=None, filters_by=None, 
            search=None, date_range=None, num_rows=10):
        self.model = model
        self.col_headers = col_headers
        self.sorts_by = sorts_by
        self.filters_by = filters_by
        self.num_rows = 10

        self.search = search
        self.date_range = date_range

        self.validate()

    def render(request, extra_context=None, templates=None):
        special_keys = [SEARCH, SORT]

        specials = {}
        for key in special_keys:
            specials[key] = request.GET.get(key,'')

        filters = {}
        for key in request.GET.keys():
            if key not in special_keys:
                if request.GET.get(key,''):
                    filters[key] = request.GET[key]

        # extract date range
        # get the query set
        # paginate results
        # render
        # extract filters
        qs = self.model.objects.filter(**filters)
        # extract search
        if specials[SEARCH]:
            # parse search
            search_dict = self.parse_query(specials[SEARCH])
            if search_dict:
                qs = qs.filter(search_dict)
        # extract sorts
        if specials[SORT]:
           qs = qs.order_by(specials[SORT])

    def parse_query(self, query_string):
        if not self.search:
            return {}
        # by default we do a like query on all search fields
        # if the query has prefixes for specific fields we do 
        # a like query only on that field
        # we allow for tokenized matches on space
        query_string = query_string.strip()
        return dict([('%__like' % sf, '[ ]%s' % query_string) for sf in self.search])
        # TODO implement per field search using prefix field:

    def validate_col_headers(self):
        # validate column headers
        # column headers should be a list of strings
        if self.col_headers and type(self.col_headers) != list:
            raise ImproperlyConfigured('col_headers should be a list of strings')
        else:
            for header in self.col_headers:
                if not header:
                    raise ImproperlyConfigured('Empty value not accepted for header')
                if type(header) != str:
                    raise ImproperlyConfigured(
                            '%s in col_headers is not a string' % str(header))
                if not hasattr(self.model, header):
                    raise ImproperlyConfigured(
                            '%s has no attribute %s' % (str(self.model), header))

    def validate_sorts_by(self):
        # validate sort fields
        # sort fields should be a list of tuples
        if self.sorts_by and type(self.sorts_by) != list:
            raise ImproperlyConfigured('sorts by should be a list of tuples or strings')
        else:
            for sort_by in self.sorts_by:
                if not sort_by:
                    raise ImproperlyConfigured('Empty value not accepted for sort by')
                if type(sort_by) == str:
                    # sort field should be field in the model
                    try:
                        f = self.model.meta.get_field(sort_by.replace('-',''))
                    except models.FieldDoesNotExist:
                        raise ImproperlyConfigured('cannot sort by %s as is not a model field'
                                % sort_by.replace('-',''))
                    # if headers are sepecified, sort field should also be present in them
                    if not sort_by.replace('-','') in self.col_headers:
                        raise ImproperlyConfigured('%s is not in col_headers, specify related header'
                                % sort_by.replace('-',''))
                if type(sort_by) == tuple:
                    # sort_by is a tuple, lets make sure its as we expect it
                    # ([-]sort_field,[header_name])
                    if len(sort_by) == 1:
                        sort_fld_name = sort_by[0].replace('-','')
                    if len(sort_by) == 2:
                        sort_fld_name = sort_by[0].replace('-','')
                        sort_header_name = sort_by[1]
                    if len(sort_by) > 2:
                        raise ImproperlyConfigured('%s is not a valid sort_by option' % str(sort_by))
                    try:
                        f = self.model.meta.get_field(sort_fld_name)
                    except models.FieldDoesNotExist:
                        raise ImproperlyConfigured('cannot sort by %s as it is not a model field'
                                % sort_fld_name)
                    if sort_fld_name in self.col_headers:
                        raise ImproperlyConfigured('%s is in col_headers related name not required'
                                % sort_fld_name)
                    else:
                        if sort_header_name not in self.col_headers:
                            raise ImproperlyConfigured('%s is not in col_headers.'
                                    % sort_header_name)
                else:
                    raise ImproperlyConfigured('%s is not a tuple or a string' % sort_by)

    def validate_filters_by(self):
        if self.filters_by and type(self.filters_by) != list:
            raise ImproperlyConfigured('filters_by is not a list')
        else:
            for filter in self.filters_by:
                if not type(filter) != str:
                    raise ImproperlyConfigured('%s filter is not a string.' % str(filter) )
                else:
                    try:
                        f = self.model.meta.get_field(filter)
                    except models.FieldDoesNotExist:
                        raise ImproperlyConfigured('cannot filter by %s as it is not a model field'
                                % filter)

    def validate_search(self):
        # search should be a list of model fields
        if self.search and type(self.search) != list:
            raise ImproperlyConfigured('search should be a list of model field names')
        else:
            for search_field in self.search:
                if type(search_field) != str:
                    raise ImproperlyConfigured(
                            'Invalid search field. %s is not a string' % search_field)
                try:
                    f = self.model.meta.get_field(search_field)
                except models.FieldDoesNotExist:
                    raise ImproperlyConfigured(
                            'Invalid search field. %s is not a %s field' 
                            % (search_field, str(self.model)))

    def validate_date_range(self):
        if self.date_range and type(self.date_range) != str:
            raise ImproperlyConfigured('%s is not a string field' % str(self.date_range))
        else:
            try:
                f = self.model.meta.get_field(self.date_range)
            except models.FieldDoesNotExist:
                raise ImproperlyConfigured(
                        '%s is not a model field. Cannot use it for date rage'
                        % self.date_range)

    def validate(self):
        self.validate_col_headers()
        self.validate_sorts_by()
        self.validate_filters_by()
        self.validate_search()
        self.validate_date_range()
