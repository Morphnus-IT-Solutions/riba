# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        return        
        # Deleting model 'PaymentOption'
        db.delete_table('accounts_paymentoption')

        # Deleting field 'DomainPaymentOptions.payment_option'
        db.delete_column('accounts_domainpaymentoptions', 'payment_option_id')


    def backwards(self, orm):
        return
        # Adding model 'PaymentOption'
        db.create_table('accounts_paymentoption', (
            ('bank_name', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
            ('is_offline', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_noninstant', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('bank_address', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('payment_delivery_address', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('bank_ifsc', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('bank_ac_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('bank_ac_no', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('complete_order_url', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('sort_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('bank_branch', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
            ('bank_ac_type', self.gf('django.db.models.fields.CharField')(default='current', max_length=100, blank=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'], null=True, blank=True)),
            ('is_online', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('payment_mode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentMode'])),
            ('location_url', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
            ('is_instant', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('in_favor_of', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
        ))
        db.send_create_signal('accounts', ['PaymentOption'])

        # Adding field 'DomainPaymentOptions.payment_option'
        db.add_column('accounts_domainpaymentoptions', 'payment_option', self.gf('django.db.models.fields.related.ForeignKey')(default='a', to=orm['accounts.PaymentOption']), keep_default=False)


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
            'feedback_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> feedback@chaupaati.com'", 'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'noreply_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> noreply@chaupaati.com'", 'max_length': '200'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> lead@chaupaati.com'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'promotions_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> promotions@chaupaati.com'", 'max_length': '200'}),
            'sale_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'share_product_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> share@chaupaati.com'", 'max_length': '500'}),
            'signature': ('django.db.models.fields.TextField', [], {}),
            'sms_mask': ('django.db.models.fields.TextField', [], {'blank': 'True'})
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
        'accounts.domainpaymentoptions': {
            'Meta': {'object_name': 'DomainPaymentOptions'},
            'client_domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.ClientDomain']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_dynamic_pm_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'order_taking_option': ('django.db.models.fields.CharField', [], {'default': "'book'", 'max_length': "'20'"})
        },
        'accounts.feed': {
            'Meta': {'object_name': 'Feed'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']"}),
            'feed_file_type': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'feed_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync_date': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'sync_type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'accounts.feedsyncdata': {
            'Meta': {'object_name': 'FeedSyncData'},
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Feed']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sync_status': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'accounts.notificationsettings': {
            'Meta': {'object_name': 'NotificationSettings'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']"}),
            'event': ('django.db.models.fields.CharField', [], {'default': "'Select notification event'", 'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'on_primary_email': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'on_primary_phone': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'on_secondary_email': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'on_secondary_phone': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'accounts.paymentgroups': {
            'Meta': {'object_name': 'PaymentGroups'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'accounts.paymentmode': {
            'Meta': {'object_name': 'PaymentMode'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentGroups']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'service_provider': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'validate_billing_info': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'accounts.storeowner': {
            'Meta': {'object_name': 'StoreOwner'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'position': ('django.db.models.fields.CharField', [], {'default': "'left'", 'max_length': '5'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Store']"})
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
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Store']", 'null': 'True', 'blank': 'True'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        'categories.store': {
            'Meta': {'object_name': 'Store'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['accounts']
