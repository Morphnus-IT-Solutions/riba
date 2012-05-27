from django.utils import simplejson
from django.http import HttpResponse, Http404
from django.conf import settings
from django.core.mail import send_mail
import solr
import logging
import re
import time
import datetime
import os
import hashlib


def solr_tags(fields, q='*:*'):
    s = solr.SolrConnection(settings.PRODUCT_SOLR)
    res = s.raw_query(q=q, wt='json', facet='true', facet_field=fields)
    result = simplejson.loads(res)['facet_counts']['facet_fields']
    r = []
    for k,v in result.items():
        r.extend(v)
    response = dict([(r[i],r[i+1]) for i in range(len(r)-1)[::2]])
    return response

def solr_paginator(q, start,rows):
    response = {}
    conn = solr.SolrConnection(settings.PRODUCT_SOLR)
    try:
        res = conn.query(q)
        numFound = int(res.results.numFound)
        results = res.next_batch(start=start,rows=rows).results
    except:
        numFound = 0
        results = []
    response['results'] = [dict(element) for element in results]
    response['count'] = numFound
    response['num_found'] = len(response['results'])
    response['has_prev'] = True
    response['has_next'] = True
    if start <= 0:
        response['has_prev'] = False
    if (start + rows) >= numFound:
        response['has_next'] = False
    return response

def add_data(data, include_fields=[]):
    if include_fields:
        for k,v in data.items():
            if k not in include_fields:
               data.pop(k) 
    solr_add(**data)

def order_add_data(data, include_fields=[]):
    if include_fields:
        for k,v in data.items():
            if k not in include_fields:
               data.pop(k) 
    order_solr_add(**data)

def solr_add(**data_dict):
    commit = data_dict.pop('__commit__',True)
    s = solr.SolrConnection(settings.PRODUCT_SOLR)
    s.add(**data_dict)
    if commit:
        s.commit()
    s.close()

def order_solr_add(**data_dict):
    commit = data_dict.pop('__commit__',True)
    s = solr.SolrConnection(settings.ORDER_SOLR)
    s.add(**data_dict)
    # Disable explicit commit
    #if commit:
    #    s.commit()
    s.close()

def solr_delete(id):
    s = solr.SolrConnection(settings.PRODUCT_SOLR)
    s.delete(id)
    s.commit()
    s.close()

def order_solr_delete(id):
    s = solr.SolrConnection(settings.ORDER_SOLR)
    s.delete(id)
    s.commit()
    s.close()

def solr_delete_query(q):
    s = solr.SolrConnection(settings.PRODUCT_SOLR)
    s.delete_query(q)
    s.commit()
    s.close()

def order_solr_delete_query(q):
    s = solr.SolrConnection(settings.ORDER_SOLR)
    s.delete_query(q)
    s.commit()
    s.close()

def order_solr_suggest(q):
    s = solr.SolrConnection(settings.ORDER_SOLR, **{
        'operation': '/terms'})
    response = s.raw_query(** {
                'terms_fl': 'suggest',
                'wt': 'json',
                'omitHeaders': 'true',
                'terms_prefix': q})
    return response
    

def order_solr_search(q, fields=None, highlight=None, score=True,
    sort=None, sort_order='asc', operation='/select', **kw):

    s = solr.SolrConnection(settings.ORDER_SOLR)
    try:
        return s.query(q, fields, highlight, score, sort, sort_order, **kw)
    except solr.SolrException, se:
        # Not logging for now
        return None

def solr_search(q, fields=None, highlight=None,
                  score=True, sort=None, sort_order="asc", operation='/select', request=None, visibility='always_visible', **params):
    if request and request.client and request.client.type:
        if request.client.type == 'franchise':
            from catalog.models import Tag
            tag = Tag.objects.filter(tag='itz')
            if tag:
                q += ' AND tag_id: %s ' % tag[0].id
    active_product_query = params.get('active_product_query', "status:active AND inStock:true AND visibility_s:%s" % (visibility))
    boost_query = params.get('boost_query', "{!boost b=max(product(order_count,0.3),1)}")
    if active_product_query:
        q += " AND %s" % active_product_query
    spell_check_q = q
    if boost_query:
        q = "%s %s" % (boost_query, q)
    s = solr.SolrConnection(settings.PRODUCT_SOLR, **{'operation':operation})
    try:
        response = s.query(q, fields, highlight, score, sort, sort_order, **params)
    except solr.SolrException, se:
        if request:
            q = 'client_id:%s AND status:active AND inStock:true' % request.client.client.id
        else:
            q = 'status:active AND inStock:true'
        response = s.query(q, fields, highlight, score, sort, sort_order, **params)
    return response

def solr_tags(fields, q='*:*'):
    s = solr.SolrConnection(settings.PRODUCT_SOLR)
    res = s.raw_query(q=q, wt='json', facet='true', facet_field=fields)
    result = simplejson.loads(res)['facet_counts']['facet_fields']
    r = []
    for k,v in result.items():
        r.extend(v)
    response = dict([(r[i],r[i+1]) for i in range(len(r)-1)[::2]])
    return response

def solr_time(t):
    dt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
    tt = time.mktime(dt.timetuple())+1e-6*dt.microsecond
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(tt))
