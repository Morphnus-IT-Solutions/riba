# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Coordinates'
        db.create_table('web_coordinates', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('banner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['web.Banner'], blank=True)),
            ('co_ordinates', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('link', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal('web', ['Coordinates'])

        # Adding field 'Banner.type'
        db.add_column('web_banner', 'type', self.gf('django.db.models.fields.CharField')(default='direct_link', max_length=50), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'Coordinates'
        db.delete_table('web_coordinates')

        # Deleting field 'Banner.type'
        db.delete_column('web_banner', 'type')


    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'confirmed_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> order@chaupaati.com'", 'max_length': '500'}),
            'confirmed_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'customer_support_no': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'dni': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'greeting_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'greeting_title': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_exclusive': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> lead@chaupaati.com'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'pg_return_url': ('django.db.models.fields.URLField', [], {'default': "'http://www.chaupaati.in'", 'max_length': '200', 'blank': 'True'}),
            'primary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'primary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'returns_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'secondary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'secondary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'share_product_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> share@chaupaati.com'", 'max_length': '500'}),
            'shipping_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'sms_mask': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'tos': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Channel'", 'max_length': '100'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'accounts.client': {
            'Meta': {'object_name': 'Client'},
            'clientdomain_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'confirmed_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> order@chaupaati.com'", 'max_length': '500'}),
            'confirmed_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'emi_amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '10', 'decimal_places': '2'}),
            'feedback_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> feedback@chaupaati.com'", 'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'noreply_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> noreply@chaupaati.com'", 'max_length': '200'}),
            'order_prefix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> lead@chaupaati.com'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'promotions_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> promotions@chaupaati.com'", 'max_length': '200'}),
            'sale_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'share_product_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> share@chaupaati.com'", 'max_length': '500'}),
            'signature': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sms_mask': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'terms_and_conditions': ('django.db.models.fields.TextField', [], {})
        },
        'accounts.clientdomain': {
            'Meta': {'object_name': 'ClientDomain'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'custom_home_page': ('django.db.models.fields.CharField', [], {'default': "'web/home/home.html'", 'max_length': '100'}),
            'default_redirect_to': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_channel': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_second_factor_auth_reqd': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'list_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'sale_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'website'", 'max_length': '25'})
        },
        'categories.category': {
            'Meta': {'object_name': 'Category'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'ext_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'google_conversion_label': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'moderate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']", 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'show_compare': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Store']", 'null': 'True', 'blank': 'True'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        'categories.store': {
            'Meta': {'object_name': 'Store'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'web.announcements': {
            'Meta': {'object_name': 'Announcements'},
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.ClientDomain']"}),
            'ends_on': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'landing_page_url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'sort_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'starts_on': ('django.db.models.fields.DateTimeField', [], {}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'})
        },
        'web.banner': {
            'Meta': {'object_name': 'Banner'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'redirect_to': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'direct_link'", 'max_length': '50'})
        },
        'web.coordinates': {
            'Meta': {'object_name': 'Coordinates'},
            'banner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['web.Banner']", 'blank': 'True'}),
            'co_ordinates': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        'web.menuitem': {
            'Meta': {'unique_together': "(('parent', 'sort_order'),)", 'object_name': 'MenuItem'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']", 'null': 'True', 'blank': 'True'}),
            'filters': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['web.MenuItem']", 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Store']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'category'", 'max_length': '25'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'})
        }
    }

    complete_apps = ['web']
