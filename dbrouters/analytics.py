class AnalyticsRouter(object):
    """A router to control all database operations on models in
    the tinla application"""

    def db_for_read(self, model, **hints):
        "Point all operations on tinla_app models to 'tinla'"
        if model._meta.app_label.startswith('analytics_'):
            return 'analytics'
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on tinla_app models to 'tinla'"
        if model._meta.app_label.startswith('analytics_'):
            return 'analytics'
        else:
            return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in tinla_app is involved"
        if obj1._meta.app_label.startswith('analytics_') or obj2._meta.app_label.startswith('analytics_'):
            return True
        return None

    def allow_syncdb(self, db, model):
        "Make sure the tinla_app app only appears on the 'tinla' db"
#        if db == 'tinla':
#            return model._meta.app_label == 'tinla_app'
#        elif model._meta.app_label == 'tinla_app':
#            return False
        return None

class ComplaintsRouter(object):
    """A router to control all database operations on models in
    the complaints application"""

    def db_for_read(self, model, **hints):
        "Point all operations on complaints models to 'complaints'"
        if model._meta.app_label == 'complaints':
            return 'complaints'
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on complaints models to 'complaints'"
#        if model._meta.app_label == 'complaints':
#            return 'complaints'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in complaints is involved"
        if obj1._meta.app_label == 'complaints' or obj2._meta.app_label == 'complaints':
            return True
        return None

    def allow_syncdb(self, db, model):
        "Make sure the complaints app only appears on the 'complaints' db"
#        if db == 'complaints':
#            return model._meta.app_label == 'complaints'
#        elif model._meta.app_label == 'complaints':
#            return False
        return None
