# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'VoucherEmailMapping'
        db.delete_table('affiliates_voucheremailmapping')

        # Deleting model 'CouponType'
        db.delete_table('affiliates_coupontype')

        # Deleting model 'Voucher'
        db.delete_table('affiliates_voucher')

        # Deleting model 'Affiliate'
        db.delete_table('affiliates_affiliate')

        # Deleting model 'CouponEmailMapping'
        db.delete_table('affiliates_couponemailmapping')

        # Deleting model 'VoucherPhoneMapping'
        db.delete_table('affiliates_voucherphonemapping')

        # Deleting model 'SubscriptionLink'
        db.delete_table('affiliates_subscriptionlink')


    def backwards(self, orm):
        
        # Adding model 'VoucherEmailMapping'
        db.create_table('affiliates_voucheremailmapping', (
            ('voucher', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['affiliates.Voucher'])),
            ('email', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.Email'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('affiliates', ['VoucherEmailMapping'])

        # Adding model 'CouponType'
        db.create_table('affiliates_coupontype', (
            ('min_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('discount_available_on', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
            ('offer', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('percentage_off', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('terms_and_conditions', self.gf('django.db.models.fields.TextField')()),
            ('discount_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('is_price_range', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('coupon_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('shopping_page', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('affiliate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['affiliates.Affiliate'], null=True, blank=True)),
            ('discount_value', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
            ('max_price', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=2, blank=True)),
        ))
        db.send_create_signal('affiliates', ['CouponType'])

        # Adding model 'Voucher'
        db.create_table('affiliates_voucher', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='inactive', max_length=25, db_index=True)),
            ('affiliate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['affiliates.Affiliate'], null=True, blank=True)),
            ('uses', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['affiliates.CouponType'], null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('expires_on', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2011, 7, 16, 16, 37, 57, 129654), null=True, blank=True)),
        ))
        db.send_create_signal('affiliates', ['Voucher'])

        # Adding model 'Affiliate'
        db.create_table('affiliates_affiliate', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, unique=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True, blank=True)),
            ('is_coupon_avail', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('affiliates', ['Affiliate'])

        # Adding model 'CouponEmailMapping'
        db.create_table('affiliates_couponemailmapping', (
            ('coupon', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['promotions.Coupon'])),
            ('email', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.Email'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('affiliates', ['CouponEmailMapping'])

        # Adding model 'VoucherPhoneMapping'
        db.create_table('affiliates_voucherphonemapping', (
            ('phone', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.Phone'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('voucher', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['affiliates.Voucher'])),
        ))
        db.send_create_signal('affiliates', ['VoucherPhoneMapping'])

        # Adding model 'SubscriptionLink'
        db.create_table('affiliates_subscriptionlink', (
            ('path', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('newsletter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['users.NewsLetter'])),
            ('affiliate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['affiliates.Affiliate'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('affiliates', ['SubscriptionLink'])


    models = {
        
    }

    complete_apps = ['affiliates']
