# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'PaymentModeParameters'
        db.delete_table('accounts_paymentmodeparameters')

        # Adding model 'PaymentOption'
        db.create_table('accounts_paymentoption', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Account'])),
            ('payment_mode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentMode'])),
        ))
        db.send_create_signal('accounts', ['PaymentOption'])

        # Adding model 'PaymentOptionSettings'
        db.create_table('accounts_paymentoptionsettings', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('payment_option', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentOption'])),
            ('parameter', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('accounts', ['PaymentOptionSettings'])

        # Deleting field 'PaymentMode.payment_mode'
        db.delete_column('accounts_paymentmode', 'payment_mode')

        # Deleting field 'PaymentMode.account'
        db.delete_column('accounts_paymentmode', 'account_id')

        # Adding field 'PaymentMode.name'
        db.add_column('accounts_paymentmode', 'name', self.gf('django.db.models.fields.CharField')(default='', max_length=25), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'PaymentModeParameters'
        db.create_table('accounts_paymentmodeparameters', (
            ('payment_mode', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.PaymentMode'])),
            ('parameter', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('accounts', ['PaymentModeParameters'])

        # Deleting model 'PaymentOption'
        db.delete_table('accounts_paymentoption')

        # Deleting model 'PaymentOptionSettings'
        db.delete_table('accounts_paymentoptionsettings')

        # Adding field 'PaymentMode.payment_mode'
        db.add_column('accounts_paymentmode', 'payment_mode', self.gf('django.db.models.fields.CharField')(default='', max_length=15), keep_default=False)

        # Adding field 'PaymentMode.account'
        db.add_column('accounts_paymentmode', 'account', self.gf('django.db.models.fields.related.ForeignKey')(default='', to=orm['accounts.Account']), keep_default=False)

        # Deleting field 'PaymentMode.name'
        db.delete_column('accounts_paymentmode', 'name')


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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'accounts.paymentoption': {
            'Meta': {'object_name': 'PaymentOption'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment_mode': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentMode']"})
        },
        'accounts.paymentoptionsettings': {
            'Meta': {'object_name': 'PaymentOptionSettings'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parameter': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'payment_option': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.PaymentOption']"}),
            'value': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['accounts']
