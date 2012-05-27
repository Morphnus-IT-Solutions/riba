# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Voucher'
        db.create_table('affiliates_voucher', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['affiliates.CouponType'])),
            ('uses', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('status', self.gf('django.db.models.fields.CharField')(default='inactive', max_length=25)),
        ))
        db.send_create_signal('affiliates', ['Voucher'])

        # Adding model 'CouponType'
        db.create_table('affiliates_coupontype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('coupon_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('terms_and_conditions', self.gf('django.db.models.fields.TextField')()),
            ('discount_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('price_range', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('min_price', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('max_price', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('percentage_off', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('discount_value', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('discount_available_on', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('affiliate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['affiliates.Affiliate'], null=True, blank=True)),
        ))
        db.send_create_signal('affiliates', ['CouponType'])

        # Changing field 'SubscriptionLink.path'
        db.alter_column('affiliates_subscriptionlink', 'path', self.gf('django.db.models.fields.CharField')(max_length=200))


    def backwards(self, orm):
        
        # Deleting model 'Voucher'
        db.delete_table('affiliates_voucher')

        # Deleting model 'CouponType'
        db.delete_table('affiliates_coupontype')

        # Changing field 'SubscriptionLink.path'
        db.alter_column('affiliates_subscriptionlink', 'path', self.gf('django.db.models.fields.URLField')(max_length=200))


    models = {
        'accounts.client': {
            'Meta': {'object_name': 'Client'},
            'confirmed_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> order@chaupaati.com'", 'max_length': '500'}),
            'confirmed_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'noreply_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> noreply@chaupaati.com'", 'max_length': '200'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> lead@chaupaati.com'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'share_product_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> share@chaupaati.com'", 'max_length': '500'}),
            'signature': ('django.db.models.fields.TextField', [], {}),
            'sms_mask': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'affiliates.affiliate': {
            'Meta': {'object_name': 'Affiliate'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'})
        },
        'affiliates.coupontype': {
            'Meta': {'object_name': 'CouponType'},
            'affiliate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['affiliates.Affiliate']", 'null': 'True', 'blank': 'True'}),
            'coupon_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'discount_available_on': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'discount_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'discount_value': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_price': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'min_price': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'percentage_off': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'price_range': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'terms_and_conditions': ('django.db.models.fields.TextField', [], {})
        },
        'affiliates.subscriptionlink': {
            'Meta': {'object_name': 'SubscriptionLink'},
            'affiliate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['affiliates.Affiliate']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.NewsLetter']"}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'affiliates.voucher': {
            'Meta': {'object_name': 'Voucher'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'inactive'", 'max_length': '25'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['affiliates.CouponType']"}),
            'uses': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'users.newsletter': {
            'Meta': {'object_name': 'NewsLetter'},
            'affiliate_logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'affiliate_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'affiliate_text': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'client': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['accounts.Client']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsletter': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['affiliates']
