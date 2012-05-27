# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'WhiteLabelStore'
        db.create_table('stores_whitelabelstore', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('header', self.gf('django.db.models.fields.CharField')(default='none', max_length=20)),
            ('footer', self.gf('django.db.models.fields.CharField')(default='none', max_length=20)),
            ('order_on_phone', self.gf('django.db.models.fields.CharField')(default='none', max_length=20)),
            ('home_page', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('category_specific_filters', self.gf('django.db.models.fields.CharField')(default='hide', max_length=20)),
            ('brand_filter', self.gf('django.db.models.fields.CharField')(default='hide', max_length=20)),
            ('category_filter', self.gf('django.db.models.fields.CharField')(default='hide', max_length=20)),
            ('breadcrumb', self.gf('django.db.models.fields.CharField')(default='hide', max_length=20)),
            ('brand_link', self.gf('django.db.models.fields.CharField')(default='hide', max_length=20)),
            ('sold_by', self.gf('django.db.models.fields.CharField')(default='hide', max_length=20)),
            ('similar_products', self.gf('django.db.models.fields.CharField')(default='hide', max_length=20)),
            ('delivery_instructions', self.gf('django.db.models.fields.CharField')(default='show', max_length=20)),
            ('gift_message', self.gf('django.db.models.fields.CharField')(default='show', max_length=20)),
        ))
        db.send_create_signal('stores', ['WhiteLabelStore'])


    def backwards(self, orm):
        
        # Deleting model 'WhiteLabelStore'
        db.delete_table('stores_whitelabelstore')


    models = {
        'stores.whitelabelstore': {
            'Meta': {'object_name': 'WhiteLabelStore'},
            'brand_filter': ('django.db.models.fields.CharField', [], {'default': "'hide'", 'max_length': '20'}),
            'brand_link': ('django.db.models.fields.CharField', [], {'default': "'hide'", 'max_length': '20'}),
            'breadcrumb': ('django.db.models.fields.CharField', [], {'default': "'hide'", 'max_length': '20'}),
            'category_filter': ('django.db.models.fields.CharField', [], {'default': "'hide'", 'max_length': '20'}),
            'category_specific_filters': ('django.db.models.fields.CharField', [], {'default': "'hide'", 'max_length': '20'}),
            'delivery_instructions': ('django.db.models.fields.CharField', [], {'default': "'show'", 'max_length': '20'}),
            'footer': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '20'}),
            'gift_message': ('django.db.models.fields.CharField', [], {'default': "'show'", 'max_length': '20'}),
            'header': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '20'}),
            'home_page': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'order_on_phone': ('django.db.models.fields.CharField', [], {'default': "'none'", 'max_length': '20'}),
            'similar_products': ('django.db.models.fields.CharField', [], {'default': "'hide'", 'max_length': '20'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'sold_by': ('django.db.models.fields.CharField', [], {'default': "'hide'", 'max_length': '20'})
        }
    }

    complete_apps = ['stores']
