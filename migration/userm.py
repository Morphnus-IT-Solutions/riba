from users.models import Profile
from migration.models import DuplicateUsers,AddressMap
from django.contrib.auth.models import User
from accounts.models import *
from datetime import datetime
import solr
import logging
log = logging.getLogger('request')

users_solr = solr.SolrConnection('http://192.168.91.101:8080/user/')

sellers = []

def solr_search(q, fields=None, highlight=None,
                  score=True, sort=None, sort_order="asc", **params):
    s = users_solr
    response = s.query(q, fields, highlight, score, sort, sort_order, **params)
    return response

def record_duplicate(original, duplicate):
    try:
        existing = DuplicateUsers.objects.get(original=original, duplicate=duplicate)
        return existing
    except DuplicateUsers.DoesNotExist:
        entry = DuplicateUsers()
        entry.original = original
        entry.duplicate = duplicate
        entry.save()
        return entry

def add_user(doc):
    if doc['mobile'] in sellers: return

    u = User()
    try:
        u = User.objects.get(username=doc['mobile'])
    except User.DoesNotExist:
        pass
    u.username = doc['mobile']
    if 'timestamp' in doc:
        u.timestamp = doc['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    else:
        if 'modificationTime' in doc:
            u.timestamp = doc['modificationTime'].strftime('%Y-%m-%d %H:%M:%S')
    u.save()

    p = Profile()
    try:
        p = Profile.objects.get(primary_phone=doc['mobile'])
        if p.id != doc['id']:
            record_duplicate(p.id, doc['id'])
            return
    except Profile.DoesNotExist:
        pass

    p.id = doc['id']
    p.user = u
    p.full_name = doc.get('name','')
    p.gender = doc.get('gender','').lower()
    if len(p.gender) > 1:
        p.gender = p.gender[0]
    if doc.get('dateOfBirth',None):
        p.date_of_birth = doc['dateOfBirth'].strftime('%Y-%m-%d')

    p.primary_phone = doc['mobile']
    p.secondary_phone = doc.get('mobile2','')

    p.primary_email = doc.get('email','').split(',')[0]
    p.secondary_email = doc.get('email2','').split(',')[0]

    p.buyer_or_seller = 'buyer'
    p.type = doc.get('type','individual')

    p.marketing_alerts = doc.get('dealAlerts','neutral')

    p.salt = doc.get('salt','')
    p.passcode = doc.get('passcode','')


    p.created_on = u.timestamp
    p.save()


def migrate_active_users():
    count_query = solr_search('isActive:true')
    total = int(str(count_query.numFound))
    batch_size = 1000
    retrieved = 0

    print 'Found total of %s users' % total

    while retrieved < total:
        print 'Fetching %s results starting from %s' % (batch_size, retrieved)
        params = {'start':retrieved,'rows':batch_size}
        batch = solr_search('isActive:true',sort='id',**params)
        retrieved += len(batch.results)
        for doc in batch.results:
            try:
                add_user(doc)
            except Exception, e:
                log.exception('Error adding doc %s' % doc['id'])

def migrate():
    migrate_active_users()

def migrate_address(doc):
    from locations.models import Address, Country
    from accounts.models import Account
    from users.models import Profile
    from utils import utils
    add = Address()
    add.type = 'user'
    add.profile = Profile.objects.get(primary_phone=doc['mobile'])
    add.name = doc.get('deliveryName','')
    add.phone = doc.get('deliveryPhone','')
    add.pincode = doc.get('pincode2','')
    if doc.get('address2','').strip():
        add.address = doc.get('address2','')
    if doc.get('country2','').strip():
        add.country = utils.get_or_create_country(doc.get('country2',''))
    else:
        add.country = Country.objects.get(name='India')
    if doc.get('state2','').strip():
        add.state = utils.get_or_create_state(doc.get('state2',''), add.country, True)
        if doc.get('city2', ''):
            add.city = utils.get_or_create_city(doc.get('city2',''), add.state, True)
    try:
        if add.address and add.city and add.country and add.state and add.profile:
            add.save()
            amap = AddressMap(address=add)
            amap.save()
    except Exception, e:
        print repr(e)


    addr = Address()
    addr.type = 'user'
    addr.profile = Profile.objects.get(primary_phone=doc['mobile'])
    addr.name = doc.get('name','')
    addr.phone = doc.get('mobile','')
    addr.pincode = doc.get('pincode','')
    if doc.get('address','').strip():
        addr.address = doc.get('address','')
    if doc.get('country','').strip():
        addr.country = utils.get_or_create_country(doc.get('country',''))
    else:
        addr.country = Country.objects.get(name='India')
    if doc.get('state','').strip():
        addr.state = utils.get_or_create_state(doc.get('state',''), addr.country, True)
        if doc.get('city', ''):
            addr.city = utils.get_or_create_city(doc.get('city',''), addr.state, True)
    try:
        if addr.address and addr.city and addr.country and addr.state and addr.profile:
            if not addr.is_same_as(add):
                addr.save()
                amap = AddressMap(address=addr)
                amap.save()
    except Exception, e:
        print repr(e)

def migrate_active_user_addresses():
    count_query = solr_search('isActive:true')
    total = int(str(count_query.numFound))
    batch_size = 1000
    retrieved = 0

    print 'Found total of %s users' % total

    while retrieved < total:
        print 'Fetching %s results starting from %s' % (batch_size, retrieved)
        params = {'start':retrieved,'rows':batch_size}
        batch = solr_search('isActive:true',sort='id',**params)
        retrieved += len(batch.results)
        for doc in batch.results:
            try:
                migrate_address(doc)
            except Exception, e:
                log.exception('Error adding doc %s' % doc['id'])

def migrate_addresses():
    migrate_active_user_addresses()
