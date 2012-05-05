# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
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

        # Adding model 'PaymentGroups'
        db.create_table('accounts_paymentgroups', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=25)),
        ))
        db.send_create_signal('accounts', ['PaymentGroups'])

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

        # Adding field 'PaymentMode.group'
        db.add_column('accounts_paymentmode', 'group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentGroups'], null=True, blank=True, default=None), keep_default=True)

        # Changing field 'PaymentMode.group_code'
        db.alter_column('accounts_paymentmode', 'group_code', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True))

        # Changing field 'PaymentMode.name'
        db.alter_column('accounts_paymentmode', 'name', self.gf('django.db.models.fields.CharField')(max_length=50))

        # Changing field 'PaymentMode.group_name'
        db.alter_column('accounts_paymentmode', 'group_name', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True))

        # Changing field 'PaymentMode.client'
        db.alter_column('accounts_paymentmode', 'client_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'], null=True, blank=True))

        # Changing field 'PaymentMode.service_provider'
        db.alter_column('accounts_paymentmode', 'service_provider', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True))

        # Adding field 'Client.order_prefix'
        db.add_column('accounts_client', 'order_prefix', self.gf('django.db.models.fields.IntegerField')(max_length=5, null=True, blank=True, default=None), keep_default=True)

        # Adding field 'Client.emi_amount'
        db.add_column('accounts_client', 'emi_amount', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=10, decimal_places=2), keep_default=True)

        # Adding field 'PaymentOption.client'
        db.add_column('accounts_paymentoption', 'client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'], null=True, blank=True, default=None), keep_default=False)

        # Changing field 'PaymentOption.bank_name'
        db.alter_column('accounts_paymentoption', 'bank_name', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True))

        # Changing field 'PaymentOption.bank_address'
        db.alter_column('accounts_paymentoption', 'bank_address', self.gf('django.db.models.fields.TextField')(null=True, blank=True))

        # Changing field 'PaymentOption.payment_delivery_address'
        db.alter_column('accounts_paymentoption', 'payment_delivery_address', self.gf('django.db.models.fields.TextField')(null=True, blank=True))

        # Changing field 'PaymentOption.bank_ifsc'
        db.alter_column('accounts_paymentoption', 'bank_ifsc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True))

        # Changing field 'PaymentOption.bank_ac_name'
        db.alter_column('accounts_paymentoption', 'bank_ac_name', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True))

        # Changing field 'PaymentOption.bank_ac_no'
        db.alter_column('accounts_paymentoption', 'bank_ac_no', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True))

        # Changing field 'PaymentOption.complete_order_url'
        db.alter_column('accounts_paymentoption', 'complete_order_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True))

        # Changing field 'PaymentOption.bank_branch'
        db.alter_column('accounts_paymentoption', 'bank_branch', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True))

        # Changing field 'PaymentOption.payment_mode'
        db.alter_column('accounts_paymentoption', 'payment_mode_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentMode'], null=True, blank=True))

        # Changing field 'PaymentOption.location_url'
        db.alter_column('accounts_paymentoption', 'location_url', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True))

        # Changing field 'PaymentOption.in_favor_of'
        db.alter_column('accounts_paymentoption', 'in_favor_of', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True))


    def backwards(self, orm):
        
        # Deleting model 'PaymentGateways'
        db.delete_table('accounts_paymentgateways')

        # Deleting model 'PaymentGroups'
        db.delete_table('accounts_paymentgroups')

        # Deleting model 'DepositPaymentOptions'
        db.delete_table('accounts_depositpaymentoptions')

        # Deleting field 'PaymentMode.group'
        db.delete_column('accounts_paymentmode', 'group_id')

        # Changing field 'PaymentMode.group_code'
        db.alter_column('accounts_paymentmode', 'group_code', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True))

        # Changing field 'PaymentMode.name'
        db.alter_column('accounts_paymentmode', 'name', self.gf('django.db.models.fields.CharField')(max_length=25))

        # Changing field 'PaymentMode.group_name'
        db.alter_column('accounts_paymentmode', 'group_name', self.gf('django.db.models.fields.CharField')(max_length=25))

        # Changing field 'PaymentMode.client'
        db.alter_column('accounts_paymentmode', 'client_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client']))

        # Changing field 'PaymentMode.service_provider'
        db.alter_column('accounts_paymentmode', 'service_provider', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True))

        # Deleting field 'Client.order_prefix'
        db.delete_column('accounts_client', 'order_prefix')

        # Deleting field 'Client.emi_amount'
        db.delete_column('accounts_client', 'emi_amount')

        # Deleting field 'PaymentOption.client'
        db.delete_column('accounts_paymentoption', 'client_id')

        # Changing field 'PaymentOption.bank_name'
        db.alter_column('accounts_paymentoption', 'bank_name', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True))

        # Changing field 'PaymentOption.bank_address'
        db.alter_column('accounts_paymentoption', 'bank_address', self.gf('django.db.models.fields.TextField')(blank=True))

        # Changing field 'PaymentOption.payment_delivery_address'
        db.alter_column('accounts_paymentoption', 'payment_delivery_address', self.gf('django.db.models.fields.TextField')(blank=True))

        # Changing field 'PaymentOption.bank_ifsc'
        db.alter_column('accounts_paymentoption', 'bank_ifsc', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True))

        # Changing field 'PaymentOption.bank_ac_name'
        db.alter_column('accounts_paymentoption', 'bank_ac_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True))

        # Changing field 'PaymentOption.bank_ac_no'
        db.alter_column('accounts_paymentoption', 'bank_ac_no', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True))

        # Changing field 'PaymentOption.complete_order_url'
        db.alter_column('accounts_paymentoption', 'complete_order_url', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True))

        # Changing field 'PaymentOption.bank_branch'
        db.alter_column('accounts_paymentoption', 'bank_branch', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True))

        # Changing field 'PaymentOption.payment_mode'
        db.alter_column('accounts_paymentoption', 'payment_mode_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentMode']))

        # Changing field 'PaymentOption.location_url'
        db.alter_column('accounts_paymentoption', 'location_url', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True))

        # Changing field 'PaymentOption.in_favor_of'
        db.alter_column('accounts_paymentoption', 'in_favor_of', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True))


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
            'order_prefix': ('django.db.models.fields.IntegerField', [], {'max_length': '5', 'null': 'True', 'blank': 'True'}),
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
            'service_provider': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
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
