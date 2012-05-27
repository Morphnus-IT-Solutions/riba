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

oath = 'I am sure'

import logging
log = logging.getLogger('request')

def clean_orders(answer):
    if answer != oath:
        return
    from orders.models import DeliveryInfo, BillingInfo, ShippingDetails, GiftInfo, SubscriptionDetails, OrderItem, Order
    from locations.models import Address
    from users.models import Profile
    from django.contrib.auth.models import User

    # Delete all order stuff
    DeliveryInfo.objects.all().delete()
    BillingInfo.objects.all().delete()
    ShippingDetails.objects.all().delete()
    GiftInfo.objects.all().delete()
    SubscriptionDetails.objects.all().delete()
    OrderItem.objects.all().delete()
    Order.objects.all().delete()

    # Delete all addresses
    Address.objects.all().delete()

def clean_users(answer):
    if answer != oath:
        return
    from users.models import Profile
    from django.contrib.auth.models import User

    # Delete user profiles
    Profile.objects.all().delete()
    User.objects.all().delete()

def clean_sessions(answer):
    from django.contrib.sessions.models import Session
    Session.objects.all().delete()

def migrate_users(answer):
    if answer != oath:
        return
    from migration import userm
    from migration.models import DuplicateUsers
    DuplicateUsers.objects.all().delete()
    userm.migrate()

def create_default_users(answer):
    from django.contrib.auth.models import User
    # we need to create agents and few superusers to use the system
    staff = [
            {"username": "hemanth", "phone": "9326164025", "name": "Hemanth Goteti", "email": "hemanth@chaupaati.in", "is_super_user": True },
            {"username": "nilesh", "phone": "9870696051", "name": "Nilesh Padariya", "email": "nilesh@chaupaati.in", "is_super_user": True },
            {"username": "zishaan", "phone": "9769001947", "name": "Zishaan Hayath", "email": "zishaan@chaupaati.in" },
            {"username": "kashyap", "phone": "9920992651", "name": "Kashyap Deorah", "email": "kashyap@chaupaati.in" },
            {"username": "amit", "phone": "9819766601", "name": "Amit Deorukhkar", "email": "amit@chaupaati.in" },
            {"username": "yashad", "phone": "9870214759", "name": "Yashad Kirtane", "email": "yashad@chaupaati.in" },
            {"username": "nikhil", "phone": "7798420680", "name": "Nikhil Vaity", "email": "nikhil@chaupaati.in" },
            {"username": "prasant", "phone": "9920543111", "name": "Prasant Sonawane", "email": "prasant@chaupaati.in" },
            {"username": "ashwin", "phone": "9867100080", "name": "Ashwin Arora", "email": "ashwin@chaupaati.in" },
            ]

    for member in staff:
        try:
            u = User.objects.get(username=member['username'])
        except User.DoesNotExist:
            if member.get('is_super_user', None) == True:
                u = User.objects.create_superuser(member['username'], member['email'], "tinlasuperuser")
            else:
                u = User.objects.create_user(member['username'], member['email'], "staff")

def migrate_orders(answer):
    if answer != oath:
        return
    from migration.ordersm import MigrateOrders
    mo = MigrateOrders()
    mo.migrate_old_orders()
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print 'Incorrect usage. Needs an argument. Valid options for argument are'
        print 'create-product-map -- creates product map'
        print 'cleanup -- cleanup'
        print 'migrate-users -- migrates users'
        print 'migrate-orders -- migrates orders'
        print 'migrate-all --- cleansup, migrates users, migrates orders'
        print 'clean-sessions --- deletes all sessions'
    else:
        action = sys.argv[1]

        if action == 'create-product-map':
            from migration.ordersm import MigrateOrders
            mo = MigrateOrders()
            mo.create_product_map()
        else:
            print 'This is going to delete data. Make sure you have backedup what you need.'
            print 'This is going to delete orders, order items, addresses, users, profiles,'
            print 'delivery info, gift info, shipping details, subscription details'
            while True:
                print 'Make the commitment to proceed: ',
                answer = sys.stdin.readline().strip()
                if answer == oath:
                    if action == 'migrate-all' or action == 'cleanup':
                        # Step 1: Clean up data which we are going to migrate
                        clean_orders(answer)
                        clean_users(answer)
                    if action == 'migrate-all' or action == 'migrate-users':
                        # Step 2: Migrate users
                        clean_users(answer)
                        migrate_users(answer)
                        create_default_users(answer)
                    if action == 'migrate-all' or action == 'migrate-orders':
                        # Step 3:
                        clean_orders(answer)
                        migrate_orders(answer)
                    if action == 'clean-sessions':
                        clean_sessions(answer)
                    if action == 'add-staff':
                        create_default_users(answer)
                    break
                else:
                    print 'Not good enough, try again'
