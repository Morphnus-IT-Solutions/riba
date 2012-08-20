# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Client'
        db.create_table('accounts_client', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('confirmed_order_email', self.gf('django.db.models.fields.CharField')(default='<Chaupaati Bazaar> order@chaupaati.com', max_length=500)),
            ('pending_order_email', self.gf('django.db.models.fields.CharField')(default='<Chaupaati Bazaar> lead@chaupaati.com', max_length=500)),
            ('noreply_email', self.gf('django.db.models.fields.CharField')(default='<Chaupaati Bazaar> noreply@chaupaati.com', max_length=200)),
            ('feedback_email', self.gf('django.db.models.fields.CharField')(default='<Chaupaati Bazaar> feedback@chaupaati.com', max_length=200)),
            ('promotions_email', self.gf('django.db.models.fields.CharField')(default='<Chaupaati Bazaar> promotions@chaupaati.com', max_length=200)),
            ('signature', self.gf('django.db.models.fields.TextField')()),
            ('terms_and_conditions', self.gf('django.db.models.fields.TextField')()),
            ('pending_order_helpline', self.gf('django.db.models.fields.CharField')(default='0-922-222-1947', max_length=25)),
            ('confirmed_order_helpline', self.gf('django.db.models.fields.CharField')(default='0-922-222-1947', max_length=25)),
            ('clientdomain_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('sms_mask', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('order_prefix', self.gf('django.db.models.fields.CharField')(default='', max_length=5, null=True, blank=True)),
        ))
        db.send_create_signal('accounts', ['Client'])

        # Adding model 'ClientDomain'
        db.create_table('accounts_clientdomain', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'])),
            ('type', self.gf('django.db.models.fields.CharField')(default='website', max_length=25)),
            ('default_redirect_to', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('is_public', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_channel', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('custom_home_page', self.gf('django.db.models.fields.CharField')(default='web/home/home.html', max_length=100)),
            ('sale_pricelist', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
            ('list_pricelist', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
        ))
        db.send_create_signal('accounts', ['ClientDomain'])

        # Adding model 'Account'
        db.create_table('accounts_account', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'])),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('is_exclusive', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('confirmed_order_email', self.gf('django.db.models.fields.CharField')(default='<Chaupaati Bazaar> order@chaupaati.com', max_length=500)),
            ('pending_order_email', self.gf('django.db.models.fields.CharField')(default='<Chaupaati Bazaar> lead@chaupaati.com', max_length=500)),
            ('share_product_email', self.gf('django.db.models.fields.CharField')(default='<Chaupaati Bazaar> share@chaupaati.com', max_length=500)),
            ('signature', self.gf('django.db.models.fields.TextField')()),
            ('pg_return_url', self.gf('django.db.models.fields.URLField')(default='http://www.chaupaati.in', max_length=200, blank=True)),
            ('pending_order_helpline', self.gf('django.db.models.fields.CharField')(default='0-922-222-1947', max_length=25)),
            ('confirmed_order_helpline', self.gf('django.db.models.fields.CharField')(default='0-922-222-1947', max_length=25)),
            ('sms_mask', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='Channel', max_length=100)),
            ('customer_support_no', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('primary_phone', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
            ('secondary_phone', self.gf('django.db.models.fields.CharField')(max_length=15, blank=True)),
            ('primary_email', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('secondary_email', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('shipping_policy', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('returns_policy', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('tos', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('dni', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('greeting_title', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('greeting_text', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('accounts', ['Account'])

        # Adding model 'NotificationSettings'
        db.create_table('accounts_notificationsettings', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Account'])),
            ('event', self.gf('django.db.models.fields.CharField')(default='Select notification event', max_length=100)),
            ('on_primary_email', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('on_secondary_email', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('on_primary_phone', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('on_secondary_phone', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('accounts', ['NotificationSettings'])

        # Adding model 'Feed'
        db.create_table('accounts_feed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Account'])),
            ('feed_url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('feed_file_type', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('sync_type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('last_sync_date', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
        ))
        db.send_create_signal('accounts', ['Feed'])

        # Adding model 'PaymentGroups'
        db.create_table('accounts_paymentgroups', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=25)),
        ))
        db.send_create_signal('accounts', ['PaymentGroups'])

        # Adding model 'PaymentMode'
        db.create_table('accounts_paymentmode', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'], null=True, blank=True)),
            ('is_grouped', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('group_code', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True)),
            ('group_name', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentGroups'], null=True, blank=True)),
            ('validate_billing_info', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('service_provider', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True)),
        ))
        db.send_create_signal('accounts', ['PaymentMode'])

        # Adding model 'PaymentOption'
        db.create_table('accounts_paymentoption', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Account'], null=True, blank=True)),
            ('payment_mode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentMode'], null=True, blank=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'], null=True, blank=True)),
            ('sort_order', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('is_instant', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_online', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_noninstant', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_offline', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('complete_order_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('in_favor_of', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('payment_delivery_address', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bank_ac_no', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('bank_ac_type', self.gf('django.db.models.fields.CharField')(default='current', max_length=100, blank=True)),
            ('bank_ac_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('bank_name', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('bank_branch', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('bank_address', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bank_ifsc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('location_url', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
        ))
        db.send_create_signal('accounts', ['PaymentOption'])

        # Adding unique constraint on 'PaymentOption', fields ['account', 'sort_order']
        db.create_unique('accounts_paymentoption', ['account_id', 'sort_order'])

        # Adding model 'DomainPaymentOptions'
        db.create_table('accounts_domainpaymentoptions', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('payment_option', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentOption'])),
            ('client_domain', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.ClientDomain'])),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_dynamic_pm_active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('order_taking_option', self.gf('django.db.models.fields.CharField')(default='book', max_length='20')),
        ))
        db.send_create_signal('accounts', ['DomainPaymentOptions'])

        # Adding model 'PaymentGateways'
        db.create_table('accounts_paymentgateways', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('payment_mode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentMode'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('card_active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('card_emi_active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
        ))
        db.send_create_signal('accounts', ['PaymentGateways'])

        # Adding model 'DepositPaymentOptions'
        db.create_table('accounts_depositpaymentoptions', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('payment_mode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentMode'])),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'])),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('bank_ac_no', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('bank_ac_type', self.gf('django.db.models.fields.CharField')(default='current', max_length=100)),
            ('bank_ac_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('bank_name', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('bank_ifsc', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('accounts', ['DepositPaymentOptions'])

        # Adding unique constraint on 'DepositPaymentOptions', fields ['client', 'bank_name']
        db.create_unique('accounts_depositpaymentoptions', ['client_id', 'bank_name'])


    def backwards(self, orm):
        
        # Deleting model 'Client'
        db.delete_table('accounts_client')

        # Deleting model 'ClientDomain'
        db.delete_table('accounts_clientdomain')

        # Deleting model 'Account'
        db.delete_table('accounts_account')

        # Deleting model 'NotificationSettings'
        db.delete_table('accounts_notificationsettings')

        # Deleting model 'Feed'
        db.delete_table('accounts_feed')

        # Deleting model 'PaymentGroups'
        db.delete_table('accounts_paymentgroups')

        # Deleting model 'PaymentMode'
        db.delete_table('accounts_paymentmode')

        # Deleting model 'PaymentOption'
        db.delete_table('accounts_paymentoption')

        # Removing unique constraint on 'PaymentOption', fields ['account', 'sort_order']
        db.delete_unique('accounts_paymentoption', ['account_id', 'sort_order'])

        # Deleting model 'DomainPaymentOptions'
        db.delete_table('accounts_domainpaymentoptions')

        # Deleting model 'PaymentGateways'
        db.delete_table('accounts_paymentgateways')

        # Deleting model 'DepositPaymentOptions'
        db.delete_table('accounts_depositpaymentoptions')

        # Removing unique constraint on 'DepositPaymentOptions', fields ['client', 'bank_name']
        db.delete_unique('accounts_depositpaymentoptions', ['client_id', 'bank_name'])


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
            'feedback_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> feedback@chaupaati.com'", 'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'noreply_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> noreply@chaupaati.com'", 'max_length': '200'}),
            'order_prefix': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> lead@chaupaati.com'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'promotions_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> promotions@chaupaati.com'", 'max_length': '200'}),
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
            'list_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'sale_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'website'", 'max_length': '25'})
        },
        'accounts.depositpaymentoptions': {
            'Meta': {'unique_together': "(('client', 'bank_name'),)", 'object_name': 'DepositPaymentOptions'},
            'bank_ac_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'bank_ac_no': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'bank_ac_type': ('django.db.models.fields.CharField', [], {'default': "'current'", 'max_length': '100'}),
            'bank_ifsc': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'bank_name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'payment_mode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentMode']"})
        },
        'accounts.domainpaymentoptions': {
            'Meta': {'object_name': 'DomainPaymentOptions'},
            'client_domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.ClientDomain']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_dynamic_pm_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'order_taking_option': ('django.db.models.fields.CharField', [], {'default': "'book'", 'max_length': "'20'"}),
            'payment_option': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentOption']"})
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
        'accounts.paymentgateways': {
            'Meta': {'object_name': 'PaymentGateways'},
            'card_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'card_emi_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'payment_mode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentMode']"})
        },
        'accounts.paymentgroups': {
            'Meta': {'object_name': 'PaymentGroups'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'accounts.paymentmode': {
            'Meta': {'object_name': 'PaymentMode'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']", 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentGroups']", 'null': 'True', 'blank': 'True'}),
            'group_code': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'group_name': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_grouped': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'service_provider': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'validate_billing_info': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'accounts.paymentoption': {
            'Meta': {'unique_together': "(('account', 'sort_order'),)", 'object_name': 'PaymentOption'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']", 'null': 'True', 'blank': 'True'}),
            'bank_ac_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'bank_ac_no': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'bank_ac_type': ('django.db.models.fields.CharField', [], {'default': "'current'", 'max_length': '100', 'blank': 'True'}),
            'bank_address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'bank_branch': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'bank_ifsc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'bank_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']", 'null': 'True', 'blank': 'True'}),
            'complete_order_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_favor_of': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_instant': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_noninstant': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_offline': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_online': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'location_url': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'payment_delivery_address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'payment_mode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentMode']", 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        }
    }

    complete_apps = ['accounts']
