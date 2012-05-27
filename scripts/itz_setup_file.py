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

from accounts.models import ClientDomain, Client, PaymentMode
from catalog.models import SellerRateChart, Tag, ProductTags, ProductVariant, Product
from franchise.models import *
from lists.models import List, ListItem
from utils.solrutils import solr_search

client = 'Future Bazaar'
client_domain = 'devitz.futurebazaar.com'
client_domain_type = 'franchise'
client_domain_code = 'FB'

payment_mode = 'Itz Cash'
group_code = 'itz-cash'

list_slug = 'itz-offer'
list_title = 'Itz Offer'
list_desc = 'Itz Offer'
list_type = 'itz_offer'

tag_name = 'itz'
tag_hero_name = 'itz_hero'

network_name = "Itz"
list_of_merchnt_keys = {
                         '3.25' : 'FUTBZR_325',
                         '5.00' : 'FUTBZR_5',
                         '6.00' : 'FUTBZR_6',
                         '8.00' : 'FUTBZR_8',
                         '10.00' : 'FUTBZR_10',
                         '12.00' : 'FUTBZR_12',
                         }

solr_search_q = ''




client = Client.objects.filter(name=client)
if client:
    print "\n\nOkay client-",client
    client_id = client[0].id
    cd = ClientDomain.objects.filter(client=client[0], domain=client_domain, type = 'franchise')
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
    
    try:
        pm = PaymentMode.objects.get(client=client[0], name = payment_mode, code = network_name, group_code =group_code, group_name = payment_mode)
        print "Okay PaymentMode - ",pm
    except:
        print payment_mode, " PaymentMode not found"
        pm = PaymentMode(client=client[0], name = payment_mode, code = network_name, group_code =group_code , group_name =payment_mode )
        pm.save()
        print "Okay PaymentMode created -",pm
        
        
    '''
    list = List.objects.filter(client=client[0], type=list_type, slug=list_slug)
    if list:
        print "Okay List-", list
        list_id = list[0].id
        list = list[0]
    else:
        print list_slug, " not found"
        list = List()
        list.client=client[0]
        list.slug=list_slug
        list.title=list_title
        list.description=list_desc
        list.type=list_type
        list.save()
        print "Okay list created -",list
        list_id = list.id
    '''
    tag = Tag.objects.filter(tag=tag_name)
    if tag:
        print "Okay Tag-", tag
        tag = tag[0]
    else:
        print tag, " not found"
        tag = Tag(tag=tag_name)
        tag.display_name = tag_name.capitalize()
        tag.save()
        print "Okay tag created -",tag
    
    tag_hero = Tag.objects.filter(tag=tag_hero_name)
    if tag_hero:
        print "Okay Tag-", tag_hero
        tag_hero = tag_hero[0]
    else:
        print tag_hero_name, " not found"
        tag_hero = Tag(tag=tag_hero_name)
        tag_hero.display_name = tag_hero_name.capitalize()
        tag_hero.save()
        print "Okay tag hero created -",tag_hero
    tag_hero_id = tag_hero.id
    print "tag_hero_id -->",tag_hero_id
    
    '''
    list = List.objects.get(id = list_id)
    listitems = list.listitem_set.select_related('sku', 'sku__product').filter(status='active')
    print "listitems----",listitems   
    '''
    try:
        network = Network.objects.get(name = network_name)
        print "Okay network-",network
        
        for percentage, key in list_of_merchnt_keys.iteritems():
            try:
                mer_key = MerchantTypeKey.objects.get(percentage = percentage, key = key)
                print "Okay merchant key -",mer_key
            except:
                try:
                    print key, " key not present."
                    merchantTypeKey = MerchantTypeKey()
                    merchantTypeKey.percentage = percentage
                    merchantTypeKey.key = key
                    merchantTypeKey.network = network
                    merchantTypeKey.save()
                    print "Okay merchant key created -",merchantTypeKey
                except:
                    print "Passing ",key
                    pass
        params = {'rows':200}
        q = 'tag_id:%s' % tag.id
        try:
            solr_result = solr_search(q, fields ='id', **params)
            prod_ids_in_solr = [int(doc['id']) for doc in solr_result.results]
            total_results = int(solr_result.numFound)
            print "Okay ",total_results," products in prod_ids_in_solr----",prod_ids_in_solr, "\n"
            
            commision_on = CommisionOn.objects.select_related('seller_rate_chart', 'product', 'commision').filter(network = network)
            if commision_on:
                error = ''
                
                count = 0
                itz_seller_chart_ids = []
                itz_product_ids = []
                for itz_prods in commision_on:
                    count += 1
                    try:
                        src = SellerRateChart.objects.get(sku= itz_prods.seller_rate_chart.sku, seller__client=client_id)
                        itz_seller_chart_ids.append(itz_prods.seller_rate_chart.id)
                        itz_product_ids.append(itz_prods.seller_rate_chart.product.id)
                    except:
                        error = 'SKU not found in SellerRateChart'
                        print "ERROR @ row: %s for commision_on: %s " % (count, itz_prods)
                
                if not error:
                    print "Okay - All CommisionOn (itz_seller_chart_ids) ---------- ",itz_seller_chart_ids
                    print "Okay - All CommisionOn (itz_product_ids) ---------- ",itz_product_ids, "\n"
                    
                    '''
                    listitems_seller_chart_ids = []
                    itz_offer_list_items = ListItem.objects.filter(list__id=list_id)
                    for item in itz_offer_list_items:
                        listitems_seller_chart_ids.append(item.sku.id)
                    print "Okay - All LisItem (listitems_seller_chart_ids) ---------- ",listitems_seller_chart_ids
                    extra_listitems_seller_chart_ids = set(listitems_seller_chart_ids) - set(itz_seller_chart_ids)
                    print "Okay - extra_listitems_seller_chart_ids --------",extra_listitems_seller_chart_ids
                    for item in extra_listitems_seller_chart_ids:
                        try:
                            listitem = ListItem.objects.filter(list__id=list_id, sku__id = item).delete()
                        except:
                            print "Error while deleting Listitem ---- ",item
                    print "Okay - extra_listitems_seller_chart_ids deletion if any successful\n"
                    '''
                    
                    tag_product_ids = []
                    product_tags = ProductTags.objects.select_related('product').filter(type=list_type)
                    for tagss in product_tags:
                        tag_product_ids.append(tagss.product.id)
                    print "Okay - All ProductTags (tag_product_ids) --------- ",tag_product_ids
                    extra_tag_product_ids = set(tag_product_ids) - set(itz_product_ids)
                    print "Okay - extra_tag_product_ids --------",extra_tag_product_ids
                    for item in extra_tag_product_ids:
                        try:
                            product_tags = ProductTags.objects.filter(type=list_type, product__id = item).delete()
                        except:
                            print "Error while deleting ProductTags ---- ",item
                    print "Okay - extra_tag_product_ids deletion if any successful\n"
                    
                    
                    count = 0
                    for itz_prods in commision_on:
                        count += 1
                        #print "itz_prods.seller_rate_chart-------",itz_prods.seller_rate_chart, " list------", list
                        '''
                        try:
                            listitem = ListItem.objects.get(list__id=list_id, sku = itz_prods.seller_rate_chart)
                            print "Okay - listitem exists -- ",listitem
                        except:
                            listitem = ListItem()
                            listitem.list = list
                            listitem.sku = itz_prods.seller_rate_chart
                            listitem.sequence = count
                            listitem.status = 'active'
                            listitem.save()
                            print "Okay - Listitem added -- %s" % itz_prods.seller_rate_chart
                        '''
                        try:
                            pt = ProductTags.objects.get(type = list_type, product = itz_prods.seller_rate_chart.product, tag=tag)
                            print "Okay - ProductTags exists -- ",itz_prods.seller_rate_chart.product
                        except ProductTags.DoesNotExist:
                            pt = ProductTags(type = list_type, product = itz_prods.seller_rate_chart.product, tag=tag)
                            pt.save()
                            print "Okay - ProductTags added -- %s" % itz_prods.seller_rate_chart.product
                        
                        if int(itz_prods.seller_rate_chart.product.id) not in prod_ids_in_solr:
                            prod_ids_in_solr.append(int(itz_prods.seller_rate_chart.product.id))
                    
                    
                    print "prod_ids_in_solr-----",prod_ids_in_solr
                    
                    products = Product.objects.filter(id__in =prod_ids_in_solr)
                    
                    for prod in products:
                        try:
                            if prod.status != 'active':
                                print "\nProduct found. But product.status is deactive on ",prod
                                #prod.status = 'active' #Remove for production
                                #prod.save() #Remove for production
                            src = SellerRateChart.objects.get(product__id = prod.id, seller__client=client_id)
                            print "Product found. Now will run solr on ---",prod, " ( pricing_maintained=" ,src.pricing_maintained,", stock_status=",src.stock_status," )"
                            if src.pricing_maintained != 'yes' or src.stock_status != 'instock':
                                #src.pricing_maintained = 'yes' #Remove for production
                                #src.stock_status = 'instock' #Remove for production
                                #src.save() #Remove for production
                                print "Product found. SellerRateChart price not yes or stock status not instock for ---",src
                            print "\n"
                            prod.update_solr_index()
                        except:
                            print "Product matching query failed or solr on it failed ---- ", prod

                else:
                    print "error - ",error
            else:
                print "commision_on empty or query failed."
        except:
            print "solr_search function not working"
    except:
        print network_name, " network not found or more than 1. Add/remove manually."
    
else:
    print client ," client nor found"

print "\n"
