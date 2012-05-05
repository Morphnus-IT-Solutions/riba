class AsteriskLogRouter(object):
    """A router to control all database operations in asterisk log"""

    def db_for_read(self, model, **hints):
        """Point all read operations for models in asterisklog to 'asteriskdb'"""
        if model._meta.app_label == 'asterisklog':
            return 'asteriskdb'
        return None

    def db_for_write(self, model, **hints):
        """Point all write operations for models in asterisklog to 'asteriskdb'"""
        if model._meta.app_label == 'asterisklog':
            return 'asteriskdb'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Don't allow relationships for models in 'asterisklog'"""
        if obj1._meta.app_label == 'asterisklog' or obj2._meta.app_label == 'asterisklog':
            return False
        return None

    def allow_syncdb(self, db, model):
        """sync 'asterisklog' only in 'asteriskdb'"""
        if db == 'asteriskdb':
            return model._meta.app_label == 'asterisklog'
        elif model._meta.app_label == 'asterisklog':
            return False
        return None
