import urllib, urllib2
import socket
from parsers.BeautifulSoup import BeautifulSoup
import logging
from dealprops.models import DailyDeal
from lists.models import List
from accounts.models import Client, ClientDomain
from spider import conf
from datetime import datetime

log = logging.getLogger('request')


def fetch_page(url):
    ''' Returns a beautifulsoup object of given url or throws an error '''
    html = ''
    try:
        proxy = urllib2.ProxyHandler({
            'http': 'http://hemango:india123@10.0.4.11:3128'})
        opener = urllib2.build_opener(proxy)
        urllib2.install_opener(opener)
        req = urllib2.Request(url)
        res = urllib2.urlopen(req)
        html = res.read()
    except IOError, e:
        log.exception('Error fetching url %s' % url)
        if hasattr(e, 'reason'):
            # Not a HTTP error. die
            raise
        if hasattr(e, 'code'):
            # Nothing defined. die again
            raise
    doc = BeautifulSoup(html)
    return doc



def get_prices(q, store):
    try:
        url = store['search_url']
        if store.get('quote_qs', False):
            q = '"%s"' % q
        params = {
            store['query_key']: q 
            }
        url = "%s%s" % (url, urllib.urlencode(params))
        log.info(url)
        doc = fetch_page(url)
        search_results = store['get_results'](doc) 
        matches = []
        #if not store['has_results'](doc):
        #    log.info('No matching results')
        #    return matches
        for result in search_results:
            try:
                title = store['get_result_title'](result)
                price = store['get_result_price'](result)
                url = store['get_result_url'](result)
                if 'http' not in url:
                    url = 'http://%s%s' % (store['domain'], url)
                matches.append({
                    'title': title.strip(),
                    'price': price.replace(' ','').replace('Rs.', '').replace(
                        ',','').split('.')[0],
                    'link': url.strip(),
                    'store': store['name']
                    })
            except Exception, e:
                log.exception('Error parsing search result')
        return matches
    except Exception,e :
        log.exception('Error fetching prices')

def get_product_page_link(q, store):
    try:
        # Lets do a google search to get the product page
        url = store['search_url']
        if store.get('quote_qs', False):
            q = '"%s"' % q
        params = {
            store['query_key']: q 
            }
        url = "%s%s" % (url, urllib.urlencode(params))
        doc = fetch_page(url)
        pdp_links = store['get_pdp_links'](doc)
        for link in pdp_links:
            # Link for a page of the store. Lets see if its a product page link
            href = link['href']
            if store.get('pdp_re', []):
                for rexp in store['pdp_re']:
                    if rexp.match(href):
                        return href
            else:
                return href
    except Exception, e:
        log.exception('Error finding product page') 

def get_price(q, store):
    try:
        page_url = get_product_page_link(q, store)
        if 'http' not in page_url:
            page_url = 'http://%s%s' % (store['domain'], page_url)
        doc = fetch_page(page_url)
        price_elem = store['get_price'](doc)
        title_elem = store['get_title'](doc)
        if price_elem:
            return {
                'store': store['name'],
                'price': price_elem[0].text.replace(
                    'Rs.','').replace(',','').replace('Rs ','').replace(' ',''),
                'title': title_elem[0].text,
                'link': page_url
                }
    except Exception, e:
        log.exception('Error finding price') 
        return {
            'store': store['name'],
            'price': '',
            'title': '',
            'link': ''
            }


def get_compare_results(q):
    comparisions =  []
    for store in conf.stores:
        result = get_prices(q, store)
        if result:
            comparisions += result
    return comparisions

def fbdeals():
    dailydeal = DailyDeal.objects.get(pk=151)
    domain = ClientDomain.objects.get(domain='www.futurebazaar.com')
    rc = dailydeal.rate_chart
    price_info = rc.get_price_for_domain(domain)
    print 'Getting prices for %s' % rc.product.title
    print 'FutureBazaar \t\t %s' % price_info['offer_price']
    for store in conf.stores:
        q = '%s %s' % (rate_chart.product.brand.name, rate_chart.product.model)
        get_price(q, store)

    battle = List.objects.get(pk=2179)
    for battle_item in battle.get_active_items():
        rc = battle_item.sku
        price_info = rc.get_price_for_domain(domain)
        print 'Getting prices for %s' % rc.product.title
        print 'FutureBazaar \t\t %s' % price_info['offer_price']
        for store in conf.stores:
            q = '%s %s' % (rc.product.brand.name, rc.product.model)
            get_price(rc, store)

