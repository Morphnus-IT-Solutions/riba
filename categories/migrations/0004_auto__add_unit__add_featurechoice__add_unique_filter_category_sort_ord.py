# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Unit'
        db.create_table('categories_unit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=150, db_index=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=150, db_index=True)),
            ('base', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['categories.Unit'], null=True, blank=True)),
            ('multiplier', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=12, decimal_places=2, blank=True)),
            ('inverse_multipler', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('categories', ['Unit'])

        # Adding model 'FeatureChoice'
        db.create_table('categories_featurechoice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('feature', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['categories.Feature'])),
        ))
        db.send_create_signal('categories', ['FeatureChoice'])

        # Adding unique constraint on 'Filter', fields ['category', 'sort_order']
        db.create_unique('categories_filter', ['category_id', 'sort_order'])

        # Deleting field 'Feature.options'
        db.delete_column('categories_feature', 'options')

        # Renaming column for 'Feature.unit' to match new field type.
        db.rename_column('categories_feature', 'unit', 'unit_id')
        # Changing field 'Feature.unit'
        db.alter_column('categories_feature', 'unit_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['categories.Unit'], null=True, blank=True))

        # Adding index on 'Feature', fields ['unit']
        db.create_index('categories_feature', ['unit_id'])

        # Adding unique constraint on 'Feature', fields ['category', 'name']
        db.create_unique('categories_feature', ['category_id', 'name'])


    def backwards(self, orm):
        
        # Deleting model 'Unit'
        db.delete_table('categories_unit')

        # Deleting model 'FeatureChoice'
        db.delete_table('categories_featurechoice')

        # Removing unique constraint on 'Filter', fields ['category', 'sort_order']
        db.delete_unique('categories_filter', ['category_id', 'sort_order'])

        # Adding field 'Feature.options'
        db.add_column('categories_feature', 'options', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Renaming column for 'Feature.unit' to match new field type.
        db.rename_column('categories_feature', 'unit_id', 'unit')
        # Changing field 'Feature.unit'
        db.alter_column('categories_feature', 'unit', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True))

        # Removing index on 'Feature', fields ['unit']
        db.delete_index('categories_feature', ['unit_id'])

        # Removing unique constraint on 'Feature', fields ['category', 'name']
        db.delete_unique('categories_feature', ['category_id', 'name'])


    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Address']", 'null': 'True', 'blank': 'True'}),
            'customer_support_no': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'managers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'primary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'primary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'returns_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'secondary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'secondary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'shipping_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'tos': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Channel'", 'max_length': '100'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'categories.category': {
            'Meta': {'object_name': 'Category'},
            'ext_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']", 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Store']"})
        },
        'categories.feature': {
            'Meta': {'unique_together': "(('name', 'category'),)", 'object_name': 'Feature'},
            'allow_multiple_select': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.FeatureGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_visible': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'max': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'min': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Unit']", 'null': 'True', 'blank': 'True'})
        },
        'categories.featurechoice': {
            'Meta': {'unique_together': "(('name', 'feature'),)", 'object_name': 'FeatureChoice'},
            'feature': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Feature']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'categories.featuregroup': {
            'Meta': {'unique_together': "(('category', 'sort_order'),)", 'object_name': 'FeatureGroup'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']"}),
            'hide_unavailable_features': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'categories.filter': {
            'Meta': {'unique_together': "(('category', 'sort_order'),)", 'object_name': 'Filter'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']"}),
            'feature': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Feature']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'categories.filtergroup': {
            'Meta': {'unique_together': "(('category', 'sort_order'),)", 'object_name': 'FilterGroup'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'categories.store': {
            'Meta': {'object_name': 'Store'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'categories.unit': {
            'Meta': {'object_name': 'Unit'},
            'base': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Unit']", 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inverse_multipler': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'multiplier': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150', 'db_index': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locations.address': {
            'Meta': {'object_name': 'Address'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']"}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_one': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'line_three': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'line_two': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'pincode': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'locations.city': {
            'Meta': {'object_name': 'City'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']", 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': "'15'", 'db_index': 'True'}),
            'user_created': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'})
        },
        'locations.country': {
            'Meta': {'object_name': 'Country'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': "'15'", 'db_index': 'True'}),
            'user_created': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'})
        },
        'locations.state': {
            'Meta': {'object_name': 'State'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': "'15'", 'db_index': 'True'}),
            'user_created': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['categories']
