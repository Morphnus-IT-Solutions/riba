import random
import logging
from django.conf import settings
log = logging.getLogger('request')

MASTER = getattr(settings, 'DB_MASTER', 'default')
SLAVE = getattr(settings, 'DB_SLAVE', 'default')

DB_LIST = (MASTER, SLAVE)

class FutureBazaarDBRouter:
    ''' DB Router for future bazaar.
        DB Router documentation at 
        http://docs.djangoproject.com/en/dev/topics/db/multi-db/
    '''

    def db_for_read(self, model, **hints):
        ''' Suggest the database that should be used for read 
            operations for objects of type model.
        '''
        if model._meta.app_label == 'atg':
            return 'atg'
        if model._meta.app_label.startswith('analytics_'):
            return 'analytics'
        if model._meta.app_label == 'complaints':
            return MASTER
        if model._meta.app_label == 'south':
            return MASTER
        if model._meta.app_label == 'orders':
            return MASTER
        if model._meta.app_label == 'locations':
            # TODO Some locations stuff can perhaps be read from slave
            return MASTER
        if model._meta.app_label == 'payments':
            return MASTER
        if model._meta.app_label == 'pricing':
            return MASTER
        if model._meta.app_label == 'users':
            return MASTER
        if model._meta.app_label == 'auth':
            return MASTER
        if model._meta.app_label == 'sessions':
            return MASTER
        if model._meta.app_label == 'catalog':
            return SLAVE
        if model._meta.app_label == 'categories':
            return SLAVE
        if model._meta.app_label == 'accounts':
            return SLAVE
        if model._meta.app_label == 'support':
            return MASTER
        if model._meta.app_label == 'fulfillment':
            return MASTER
        if model._meta.app_label == 'inventory':
            return MASTER

        # Split the reads between master and slave
        return random.choice([MASTER, SLAVE])

    def db_for_write(self, model, **hints):
        ''' Suggest the database that should be used for writes of 
            objects of type Model.
        '''
        if model._meta.app_label == 'atg':
            return 'atg'
        if model._meta.app_label.startswith('analytics_'):
            return 'analytics'
        return MASTER

    def allow_relation(self, obj1, obj2, **hints):
        ''' Return True if a relation between obj1 and obj2 should be allowed,
            False if the relation should be prevented, or None if the router 
            has no opinion. This is purely a validation operation, used by 
            foreign key and many to many operations to determine if a relation
            should be allowed between two objects.
        '''
        if obj1._state.db in DB_LIST and obj2._state.db in DB_LIST:
            return True
        if obj1._meta.app_label.startswith('analytics_') or obj2._meta.app_label.startswith('analytics_'):
            return True
        if obj1._meta.app_label == 'complaints' or obj2._meta.app_label == 'complaints':
            return True
        return None

    def allow_syncdb(self, db, model):
        ''' Determine if the model should be synchronized onto the database with
            alias db. Return True if the model should be synchronized, False if 
            it should not be synchronized, or None if the router has no opinion.
            This method can be used to determine the availability of a model on a
            given database.
        '''
        if model._meta.app_label == 'atg':
            if db == 'atg':
                return True
            else:
                return False
        return True
