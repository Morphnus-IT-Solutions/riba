# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BrandBlackLists'
        db.create_table('feeds_brandblacklists', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brand', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
        ))
        db.send_create_signal('feeds', ['BrandBlackLists'])

        # Adding unique constraint on 'BrandBlackLists', fields ['brand', 'account']
        db.create_unique('feeds_brandblacklists', ['brand', 'account'])

        # Adding model 'CategoryBlackLists'
        db.create_table('feeds_categoryblacklists', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
        ))
        db.send_create_signal('feeds', ['CategoryBlackLists'])

        # Adding unique constraint on 'CategoryBlackLists', fields ['category', 'account']
        db.create_unique('feeds_categoryblacklists', ['category', 'account'])


    def backwards(self, orm):
        
        # Deleting model 'BrandBlackLists'
        db.delete_table('feeds_brandblacklists')

        # Removing unique constraint on 'BrandBlackLists', fields ['brand', 'account']
        db.delete_unique('feeds_brandblacklists', ['brand', 'account'])

        # Deleting model 'CategoryBlackLists'
        db.delete_table('feeds_categoryblacklists')

        # Removing unique constraint on 'CategoryBlackLists', fields ['category', 'account']
        db.delete_unique('feeds_categoryblacklists', ['category', 'account'])


    models = {
        'feeds.brandblacklists': {
            'Meta': {'unique_together': "(('brand', 'account'),)", 'object_name': 'BrandBlackLists'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'brand': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'feeds.categoryblacklists': {
            'Meta': {'unique_together': "(('category', 'account'),)", 'object_name': 'CategoryBlackLists'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['feeds']
