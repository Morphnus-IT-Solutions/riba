# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'BrandBlackLists'
        db.delete_table('feeds_brandblacklists')

        # Deleting model 'CategoryBlackLists'
        db.delete_table('feeds_categoryblacklists')

        # Adding model 'CategoryBlackList'
        db.create_table('feeds_categoryblacklist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
        ))
        db.send_create_signal('feeds', ['CategoryBlackList'])

        # Adding model 'SKUBlackList'
        db.create_table('feeds_skublacklist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sku', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
        ))
        db.send_create_signal('feeds', ['SKUBlackList'])

        # Adding model 'SKUInfo'
        db.create_table('feeds_skuinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sku', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('brand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Brand'], null=True, blank=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['categories.Category'], null=True, blank=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Product'], null=True, blank=True)),
        ))
        db.send_create_signal('feeds', ['SKUInfo'])

        # Adding model 'CategoryMapping'
        db.create_table('feeds_categorymapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('mapped_to', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['categories.Category'])),
        ))
        db.send_create_signal('feeds', ['CategoryMapping'])

        # Adding model 'BrandBlackList'
        db.create_table('feeds_brandblacklist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brand', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
        ))
        db.send_create_signal('feeds', ['BrandBlackList'])

        # Adding model 'BrandMapping'
        db.create_table('feeds_brandmapping', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brand', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('mapped_to', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['catalog.Brand'])),
        ))
        db.send_create_signal('feeds', ['BrandMapping'])


    def backwards(self, orm):
        
        # Adding model 'BrandBlackLists'
        db.create_table('feeds_brandblacklists', (
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('brand', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('feeds', ['BrandBlackLists'])

        # Adding model 'CategoryBlackLists'
        db.create_table('feeds_categoryblacklists', (
            ('category', self.gf('django.db.models.fields.CharField')(max_length=200, db_index=True)),
            ('account', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('feeds', ['CategoryBlackLists'])

        # Deleting model 'CategoryBlackList'
        db.delete_table('feeds_categoryblacklist')

        # Deleting model 'SKUBlackList'
        db.delete_table('feeds_skublacklist')

        # Deleting model 'SKUInfo'
        db.delete_table('feeds_skuinfo')

        # Deleting model 'CategoryMapping'
        db.delete_table('feeds_categorymapping')

        # Deleting model 'BrandBlackList'
        db.delete_table('feeds_brandblacklist')

        # Deleting model 'BrandMapping'
        db.delete_table('feeds_brandmapping')


    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'customer_support_no': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        'catalog.brand': {
            'Meta': {'object_name': 'Brand'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'catalog.product': {
            'Meta': {'object_name': 'Product'},
            'brand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Brand']"}),
            'cart_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']"}),
            'confirmed_order_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'inr'", 'max_length': '3'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'has_images': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'pending_order_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Available'", 'max_length': '15', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'normal'", 'max_length': '10'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
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
        'categories.store': {
            'Meta': {'object_name': 'Store'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'feeds.brandblacklist': {
            'Meta': {'unique_together': "(('brand', 'account'),)", 'object_name': 'BrandBlackList'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'brand': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'feeds.brandmapping': {
            'Meta': {'unique_together': "(('brand', 'account'),)", 'object_name': 'BrandMapping'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'brand': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mapped_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Brand']"})
        },
        'feeds.categoryblacklist': {
            'Meta': {'unique_together': "(('category', 'account'),)", 'object_name': 'CategoryBlackList'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'feeds.categorymapping': {
            'Meta': {'unique_together': "(('category', 'account'),)", 'object_name': 'CategoryMapping'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'category': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mapped_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']"})
        },
        'feeds.skublacklist': {
            'Meta': {'unique_together': "(('sku', 'account'),)", 'object_name': 'SKUBlackList'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'})
        },
        'feeds.skuinfo': {
            'Meta': {'unique_together': "(('sku', 'account'),)", 'object_name': 'SKUInfo'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'brand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Brand']", 'null': 'True', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Product']", 'null': 'True', 'blank': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'})
        }
    }

    complete_apps = ['feeds']
