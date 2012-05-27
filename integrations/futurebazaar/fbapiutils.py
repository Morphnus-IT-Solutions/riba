from suds.client import Client
#from django.conf import settings

def get_client(component, method):
    print get_url_for(component, method)
    return Client(
            get_url_for(component, method)
        )

def get_url_for(component, method):
    #url = 'http://shop.futurebazaar.com:8080'
    url = 'http://alpha.futurebazaar.com'
    #url = 'http://10.0.103.13:80'
    if component == 'user':
        url = '%s/userprofiling/usersession' % url
    if component == 'commerce':
        url = '%s/commerce/order' % url
    return '%s/%s?WSDL' % (url, method)

def xpath_s(xml_doc, namespaces, key, default=None):
    matches = xml_doc.xpath(key, namespaces=namespaces)
    if not matches:
        return default
    if len(matches) < 1:
        return default
    return matches[0].text
