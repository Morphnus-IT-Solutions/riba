# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'FeatureMapping.sku_type'
        db.alter_column('feeds_featuremapping', 'sku_type', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True))


    def backwards(self, orm):
        
        # Changing field 'FeatureMapping.sku_type'
        db.alter_column('feeds_featuremapping', 'sku_type', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True))


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
            'list_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'noreply_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> noreply@chaupaati.com'", 'max_length': '200'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> lead@chaupaati.com'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'promotions_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> promotions@chaupaati.com'", 'max_length': '200'}),
            'sale_pricelist': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'share_product_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> share@chaupaati.com'", 'max_length': '500'}),
            'signature': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sms_mask': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'catalog.availability': {
            'Meta': {'object_name': 'Availability'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'catalog.brand': {
            'Meta': {'object_name': 'Brand'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'moderate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        'catalog.product': {
            'Meta': {'object_name': 'Product'},
            'brand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Brand']"}),
            'cart_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']"}),
            'confirmed_order_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'inr'", 'max_length': '3'}),
            'description': ('tinymce.models.HTMLField', [], {}),
            'ext_large_image_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'ext_medium_image_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'ext_small_image_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'has_images': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'moderate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'pending_order_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'product_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.ProductType']", 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '150', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'normal'", 'max_length': '10'}),
            'video_embed': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'catalog.sellerratechart': {
            'Meta': {'object_name': 'SellerRateChart'},
            'article_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'availability': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Availability']"}),
            'cashback_amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'cod_available_at': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cod_available_at'", 'null': 'True', 'to': "orm['catalog.Availability']"}),
            'cod_charge': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'condition': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '5', 'db_index': 'True'}),
            'detailed_desc': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'external_product_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'external_product_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'gift_desc': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'gift_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'home_deliverable': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_cod_available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_fmemi_available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_free_shipping': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_prefered': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_so_available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'key_feature': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'list_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'max_shipping': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'min_shipping': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'offer_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'otc': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'payment_charges_paid_by': ('django.db.models.fields.CharField', [], {'default': "'chaupaati'", 'max_length': '15'}),
            'payment_collection_charges': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Product']"}),
            'seller': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products_offered'", 'to': "orm['accounts.Account']"}),
            'ship_local_only': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'shipping_duration': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'shipping_paid_by': ('django.db.models.fields.CharField', [], {'default': "'vendor'", 'max_length': '15'}),
            'shipping_percent': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '4', 'decimal_places': '2'}),
            'short_desc': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'stock_status': ('django.db.models.fields.CharField', [], {'default': "'instock'", 'max_length': '100'}),
            'transfer_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'visibility_status': ('django.db.models.fields.CharField', [], {'default': "'always_visible'", 'max_length': '100', 'db_index': 'True'}),
            'warranty': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'whats_in_the_box': ('django.db.models.fields.TextField', [], {'blank': 'True'})
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
        'categories.feature': {
            'Meta': {'object_name': 'Feature'},
            'allow_multiple_select': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']", 'null': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.FeatureGroup']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index_for_presence': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_visible': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'max': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'min': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'product_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.ProductType']", 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Unit']", 'null': 'True', 'blank': 'True'}),
            'use_as_key_features': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'use_for_icons': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'categories.featurechoice': {
            'Meta': {'unique_together': "(('name', 'feature'),)", 'object_name': 'FeatureChoice'},
            'feature': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Feature']"}),
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'categories.featuregroup': {
            'Meta': {'unique_together': "(('product_type', 'name'),)", 'object_name': 'FeatureGroup'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Category']", 'null': 'True', 'blank': 'True'}),
            'hide_unavailable_features': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'product_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.ProductType']", 'null': 'True', 'blank': 'True'}),
            'sort_order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'categories.producttype': {
            'Meta': {'unique_together': "(('type', 'client'),)", 'object_name': 'ProductType'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'categories.store': {
            'Meta': {'object_name': 'Store'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'categories.unit': {
            'Meta': {'object_name': 'Unit'},
            'base': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Unit']", 'null': 'True', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inverse_multipler': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'multiplier': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '150', 'db_index': 'True'})
        },
        'feeds.apiresponse': {
            'Meta': {'object_name': 'APIResponse'},
            'client': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'login': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'order_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'post': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'response': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'session_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'})
        },
        'feeds.availabilitymap': {
            'Meta': {'object_name': 'AvailabilityMap'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'applies_to': ('django.db.models.fields.CharField', [], {'default': "'account'", 'max_length': '25', 'db_index': 'True'}),
            'availability': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Availability']"}),
            'brand': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'category': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'})
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
        'feeds.extpricelist': {
            'Meta': {'object_name': 'ExtPricelist'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'offer_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'priceList': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pricing.PriceList']"}),
            'rate_chart': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.SellerRateChart']"})
        },
        'feeds.featuremapping': {
            'Meta': {'object_name': 'FeatureMapping'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'action': ('django.db.models.fields.CharField', [], {'default': "'add'", 'max_length': '10'}),
            'bool': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'brand_mapping': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.BrandMapping']", 'null': 'True', 'blank': 'True'}),
            'category_mapping': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.CategoryMapping']", 'null': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'feature': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Feature']"}),
            'feature_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sku_type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'skuinfo': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.SKUInfo']", 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'})
        },
        'feeds.featureselectedchoice': {
            'Meta': {'unique_together': "(('choice', 'feature_mapping'),)", 'object_name': 'FeatureSelectedChoice'},
            'choice': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.FeatureChoice']"}),
            'feature_mapping': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.FeatureMapping']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
            'model': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Product']", 'null': 'True', 'blank': 'True'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'})
        },
        'feeds.skutypeproducttypemapping': {
            'Meta': {'object_name': 'SkuTypeProductTypeMapping'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.ProductType']"}),
            'sku_type': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'})
        },
        'feeds.subscriptionsync': {
            'Meta': {'object_name': 'SubscriptionSync'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'ext_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'feeds.syncevent': {
            'Meta': {'object_name': 'SyncEvent'},
            'account': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'adds': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'deletes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'edits': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ended_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'found': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'new_masters': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'stack_trace': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'running'", 'max_length': '25'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'unavailable': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'feeds.synceventproductmapping': {
            'Meta': {'object_name': 'SyncEventProductMapping'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '25', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Product']"}),
            'sku': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'db_index': 'True', 'blank': 'True'}),
            'sync_event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.SyncEvent']"})
        },
        'feeds.synceventratechartmapping': {
            'Meta': {'object_name': 'SyncEventRateChartMapping'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '25', 'db_index': 'True'}),
            'change_log': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'rate_chart': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.SellerRateChart']"}),
            'sku': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'db_index': 'True', 'blank': 'True'}),
            'sync_event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['feeds.SyncEvent']"})
        },
        'pricing.pricelist': {
            'Meta': {'object_name': 'PriceList'},
            'currency': ('django.db.models.fields.CharField', [], {'default': "'inr'", 'max_length': '3'}),
            'exchange_rate': ('django.db.models.fields.DecimalField', [], {'default': '1', 'max_digits': '4', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_price_label': ('django.db.models.fields.CharField', [], {'default': "'List Price'", 'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'offer_price_label': ('django.db.models.fields.CharField', [], {'default': "'Offer Price'", 'max_length': '100'})
        }
    }

    complete_apps = ['feeds']
