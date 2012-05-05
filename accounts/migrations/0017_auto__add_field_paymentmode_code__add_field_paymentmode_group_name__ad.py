# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'PaymentMode.code'
        db.add_column('accounts_paymentmode', 'code', self.gf('django.db.models.fields.CharField')(default='', max_length=25), keep_default=False)

        # Adding field 'PaymentMode.group_name'
        db.add_column('accounts_paymentmode', 'group_name', self.gf('django.db.models.fields.CharField')(default='', max_length=25), keep_default=False)

        # Adding field 'PaymentOption.complete_order_url'
        db.add_column('accounts_paymentoption', 'complete_order_url', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'PaymentOption.in_favor_of'
        db.add_column('accounts_paymentoption', 'in_favor_of', self.gf('django.db.models.fields.CharField')(default='', max_length=300, blank=True), keep_default=False)

        # Adding field 'PaymentOption.payment_delivery_address'
        db.add_column('accounts_paymentoption', 'payment_delivery_address', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'PaymentOption.bank_ac_no'
        db.add_column('accounts_paymentoption', 'bank_ac_no', self.gf('django.db.models.fields.CharField')(default='', max_length=50, blank=True), keep_default=False)

        # Adding field 'PaymentOption.bank_ac_type'
        db.add_column('accounts_paymentoption', 'bank_ac_type', self.gf('django.db.models.fields.CharField')(default='current', max_length=100, blank=True), keep_default=False)

        # Adding field 'PaymentOption.bank_ac_name'
        db.add_column('accounts_paymentoption', 'bank_ac_name', self.gf('django.db.models.fields.CharField')(default='', max_length=200, blank=True), keep_default=False)

        # Adding field 'PaymentOption.bank_name'
        db.add_column('accounts_paymentoption', 'bank_name', self.gf('django.db.models.fields.CharField')(default='', max_length=300, blank=True), keep_default=False)

        # Adding field 'PaymentOption.bank_branch'
        db.add_column('accounts_paymentoption', 'bank_branch', self.gf('django.db.models.fields.CharField')(default='', max_length=300, blank=True), keep_default=False)

        # Adding field 'PaymentOption.bank_address'
        db.add_column('accounts_paymentoption', 'bank_address', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'PaymentOption.bank_ifsc'
        db.add_column('accounts_paymentoption', 'bank_ifsc', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'PaymentMode.code'
        db.delete_column('accounts_paymentmode', 'code')

        # Deleting field 'PaymentMode.group_name'
        db.delete_column('accounts_paymentmode', 'group_name')

        # Deleting field 'PaymentOption.complete_order_url'
        db.delete_column('accounts_paymentoption', 'complete_order_url')

        # Deleting field 'PaymentOption.in_favor_of'
        db.delete_column('accounts_paymentoption', 'in_favor_of')

        # Deleting field 'PaymentOption.payment_delivery_address'
        db.delete_column('accounts_paymentoption', 'payment_delivery_address')

        # Deleting field 'PaymentOption.bank_ac_no'
        db.delete_column('accounts_paymentoption', 'bank_ac_no')

        # Deleting field 'PaymentOption.bank_ac_type'
        db.delete_column('accounts_paymentoption', 'bank_ac_type')

        # Deleting field 'PaymentOption.bank_ac_name'
        db.delete_column('accounts_paymentoption', 'bank_ac_name')

        # Deleting field 'PaymentOption.bank_name'
        db.delete_column('accounts_paymentoption', 'bank_name')

        # Deleting field 'PaymentOption.bank_branch'
        db.delete_column('accounts_paymentoption', 'bank_branch')

        # Deleting field 'PaymentOption.bank_address'
        db.delete_column('accounts_paymentoption', 'bank_address')

        # Deleting field 'PaymentOption.bank_ifsc'
        db.delete_column('accounts_paymentoption', 'bank_ifsc')


    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'confirmed_order_email': ('django.db.models.fields.CharField', [], {'default': "'order@chaupaati.in'", 'max_length': '500'}),
            'confirmed_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'customer_support_no': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'dni': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'greeting_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'greeting_title': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_exclusive': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'lead@chaupaati.in'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'primary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'primary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'returns_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'secondary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'secondary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'shipping_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'signature': ('django.db.models.fields.TextField', [], {}),
            'tos': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'track_url_prefix': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Channel'", 'max_length': '100'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
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
            'event': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'on_primary_email': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'on_primary_phone': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'on_secondary_email': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'on_secondary_phone': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'accounts.paymentmode': {
            'Meta': {'object_name': 'PaymentMode'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'group_name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'accounts.paymentoption': {
            'Meta': {'object_name': 'PaymentOption'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']"}),
            'bank_ac_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'bank_ac_no': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'bank_ac_type': ('django.db.models.fields.CharField', [], {'default': "'current'", 'max_length': '100', 'blank': 'True'}),
            'bank_address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'bank_branch': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'bank_ifsc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'bank_name': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'complete_order_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_favor_of': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'payment_delivery_address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'payment_mode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentMode']"})
        },
        'accounts.paymentoptionsettings': {
            'Meta': {'object_name': 'PaymentOptionSettings'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'payment_option': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentOption']"}),
            'value': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['accounts']
