from users.models import Profile, Phone, Email
from django.contrib.auth.models import User
from atg.models import DpsUser, DcsppOrder, FtbOrder
from migration.models import AtgUserMigrationMap
import re
from django.core.validators import email_re
from django import db
import logging
log = logging.getLogger('migration')
phone_re = re.compile('\d+')

def safe_convert(text, size, default_to=None):
    ''' Converts given text to ascii, truncates to size '''
    if text == None:
        return default_to
    return text.encode('ascii','ignore')[:size]

def new_profile(atg_user, phone, email):
    # Ensure that there is no profile with this atg login
    map_entry = None
    try:
        map_entry = AtgUserMigrationMap.objects.select_related('profile').get(
            atg_login = safe_convert(atg_user.login, 40))
        #log.info("Already migrated %s, skipping new_profile" % atg_user.login)
        return map_entry.profile
    except AtgUserMigrationMap.DoesNotExist:
        pass

    # Create a new profile
    try:
        auth_user = User()
        auth_user.username = safe_convert(atg_user.login, 40)
        auth_user.email = ''
        auth_user.password = '%s$%s$%s' % ('md5', '', atg_user.password)
        auth_user.save()
    except Exception, e:
        log.exception('Error creating auth_user for %s' % atg_user.login)
        return

    p = Profile()
    p.user = auth_user
    p.full_name = '%s %s %s' % (safe_convert(atg_user.first_name, 40, ''),
        safe_convert(atg_user.middle_name, 40, ''),
        safe_convert(atg_user.last_name, 40, ''))
    p.full_name = re.sub(' +', ' ', p.full_name) # Remove multiple spaces
    p.atg_login = safe_convert(atg_user.login, 40) 
    p.atg_password = safe_convert(atg_user.password, 35)
    p.save() # Save the profile

    map_entry = AtgUserMigrationMap(profile = p,
        atg_login = safe_convert(atg_user.login, 40))
    map_entry.save()

    if phone:
        phone.user = p
        phone.save()

    if email:
        email.user = p
        email.save()

    return p

import gc

def queryset_iterator(queryset, chunksize=1000):
    '''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    '''
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()
        
def migrate():
    # Migration plan
    # Read user, user address book from atg
    # Create one user in tinla per atg user

    #ezone_orders_users = FtbOrder.objects.select_related('order').all().values(
    #    'order__profile').distinct()
    #atg_users = DpsUser.objects.filter(dps_id__in = ezone_orders_users)
    atg_users = DpsUser.objects.all()
        
    count = atg_users.count()
    log.info('Found %s users in atg.' % count)
    index = 0
    exists = 0
    non_existing = 0
    newly_created = 0
    migrated = 0
    errors = 0
    attached = 0
    not_attached = 0
    atg_users = queryset_iterator(atg_users)
    for atg_user in atg_users:
        index += 1
        db.reset_queries()
        # Check if username is already taken in tinla
        # Tinla's usernames are phone numbers and email addresses
        email = None
        phone = None
        profile = None
        auth_user = None
        found = False
        username = atg_user.login
        try:
            email = Email.objects.select_related('user', 'user__user').get(email=username)
            profile = email.user
            auth_user = profile.user
            found = True
        except Email.DoesNotExist:
            try:
                phone = Phone.objects.select_related('user', 'user__user').get(phone=username[:10])
                profile = phone.user
                auth_user = profile.user
                found = True
            except Phone.DoesNotExist:
                pass
        if found:
            exists += 1
            if profile.atg_login:
                migrated += 1
                if profile.atg_login != username:
                    log.info('Skipping user: %s. Check if it matches with: %s' % (username, profile.atg_login))
            else:
                try:
                    profile.atg_login = username
                    profile.atg_password= atg_user.password
                    profile.save()
                    log.info('User exists. Just mapping atg_login and atg_password %s' % username)
                    attached += 1
                except:
                    log.info('User exists. Duplicate atg_login %s' % username)
                    not_attached += 1
        else:
            non_existing += 1
            log.info('%s not found in tinla' % username)
            # No email and phone taken. 
            if phone_re.match(username):
                phone = Phone(phone=username[:10])
            if email_re.match(username):
                email = Email(email=username)
            try:
                profile = new_profile(atg_user, phone, email)
                if profile:
                    newly_created += 1
                    log.info('Created new profile for %s. id is %s' % (username,
                        profile.id))
            except Exception, e:
                errors += 1
                log.exception('Error migrating %s. %s' % (username, repr(e)))

        if index % 10000 == 0:
            log.info('Processed %s/%s' % (index, count))

    log.info('Atg users: %s' % count)
    log.info('Existing: %s' % exists)
    log.info('Attached: %s' % attached)
    log.info('Not Attached: %s' % not_attached)
    log.info('Migrated by us: %s' % migrated)
    log.info('Non Existing: %s' % non_existing)
    log.info('Created: %s' % newly_created)
    log.info('Errors: %s' % errors)


if __name__ == '__main__':
    migrate()
