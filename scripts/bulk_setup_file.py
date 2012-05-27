import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from accounts.models import ClientDomain, Client
from catalog.models import SellerRateChart, Tag, ProductTags, ProductVariant, Product
from franchise.models import *
from lists.models import List, ListItem
from utils.solrutils import solr_search

client = 'Future Bazaar'
client_domain = 'devbulk.futurebazaar.com'
client_domain_type = 'website'
client_domain_code = 'FB'

client = Client.objects.filter(name=client)
if client:
    print "\n\nOkay client-",client
    client_id = client[0].id
    cd = ClientDomain.objects.filter(client=client[0], domain=client_domain, type = client_domain_type)
    if cd:
        print "Okay ClientDomain-",cd
    else:
        print client_domain," ClientDomain not found"
        cd = ClientDomain()
        cd.domain = client_domain
        cd.client = client[0]
        cd.type = client_domain_type
        cd.code = client_domain_code
        cd.save()
        print "Okay ClientDomain created -",cd
        client_id = client.id
    
else:
    print client ," client not found"

print "\n"
