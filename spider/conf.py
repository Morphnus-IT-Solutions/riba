import re

flipkart = {
    'name': 'Flipkart',
    'search_url': 'http://www.flipkart.com/search/a/all?',
    'domain': 'www.flipkart.com', 
    'query_key': 'query',
    'has_results': lambda doc: "0 items" in doc.findAll('span', {
        'id': 'allresults_info'})[0].text.strip().lower(),
    'get_pdp_links': lambda doc: doc.findAll('a', {
        'class': 'fk-srch-title-text fksd-bodytext'}),
    'get_price': lambda doc: doc.findAll('span', {
        'class': 'price final-price our fksk-our'}),
    'get_title': lambda doc: doc.findAll('div', {
        'class': 'mprod-summary-title fksk-mprod-summary-title'})[0].findAll(
        'h1'),
    'get_results': lambda doc: doc.findAll(
        'div', {'class': 'line fk-srch-item fksd-bodytext'}),
    'get_result_title': lambda doc: doc.findAll(
        'h2', {'class': 'fk-srch-item-title fksd-bodytext'})[0].text,
    'get_result_url': lambda doc: doc.findAll(
        'h2', {'class': 'fk-srch-item-title fksd-bodytext'})[0].findAll('a')[0]['href'],
    'get_result_price': lambda doc: doc.findAll(
        'b', {'class': 'fksd-bodytext price final-price'})[0].text
}

letsbuy = {
    'name': 'LetsBuy',
    'domain': 'www.letsbuy.com',
    'search_url': 'http://www.letsbuy.com/advanced_search_result.php?',
    'query_key': 'keywords',
    'has_results': lambda doc: "found 0" in doc.findAll('h1', {
        'class': 'search_head'})[0].text.strip().lower(), 
    'get_pdp_links': lambda doc: doc.findAll('div', {
        'class': 'detailbox'})[0].findAll('a'),
    'get_price': lambda doc: doc.findAll('span', {
        'class': 'offer_price'}),
    'get_title': lambda doc: doc.findAll('h1', {
        'class': 'prod_name hundred_perc'}),
    'get_results': lambda doc: doc.findAll(
        'div', {'class': 'detailbox'}),
    'get_result_title': lambda doc: doc.findAll(
        'h2', {'class': 'green'})[0].text,
    'get_result_url': lambda doc: doc.findAll(
        'h2', {'class': 'green'})[0].findAll('a')[0]['href'],
    'get_result_price': lambda doc: doc.findAll(
        'span', {'class': 'text12_stb'})[0].text
}

infibeam = {
    'name': 'Infibeam',
    'domain': 'www.infibeam.com',
    'search_url': 'http://www.infibeam.com/search?',
    'query_key': 'q',
    'quote_qs': True,
    'has_results': lambda doc: "not matchy any" in doc.findAll('div', {
        'id': 'search_result'})[0].text.strip().lower(),
    'get_pdp_links': lambda doc: doc.findAll('a', {
        'class': ''}),
    'get_price': lambda doc: doc.findAll('span', {
        'class': ''}),
    'get_results': lambda doc: doc.findAll('ul', {
        'class': 'search_result'})[0].findAll('li'),
    'get_result_title': lambda doc: doc.findAll('span', {
        'class': 'title'})[0].text,
    'get_result_url': lambda doc: doc.findAll('span', {
        'class': 'title'})[0].findAll('a')[0]['href'],
    'get_result_price': lambda doc: doc.findAll('div', {
        'class': 'price'})[0].findAll('b')[0].text
}

stores = [flipkart, letsbuy, infibeam]
