# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Order.timestamp'
        db.alter_column('orders_order', 'timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True))


    def backwards(self, orm):
        
        # Changing field 'Order.timestamp'
        db.alter_column('orders_order', 'timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True))


    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'customer_support_no': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'dni': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'greeting_text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'greeting_title': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'primary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'primary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'returns_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'secondary_email': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'secondary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'shipping_policy': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'tos': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'Channel'", 'max_length': '100'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'catalog.availability': {
            'Meta': {'object_name': 'Availability'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'catalog.brand': {
            'Meta': {'object_name': 'Brand'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'moderate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
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
            'has_images': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meta_description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'moderate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'page_title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'pending_order_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '150', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'Available'", 'max_length': '15', 'db_index': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'normal'", 'max_length': '10'}),
            'video_embed': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'catalog.sellerratechart': {
            'Meta': {'object_name': 'SellerRateChart'},
            'availability': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Availability']"}),
            'cod_available_at': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cod_available_at'", 'null': 'True', 'to': "orm['catalog.Availability']"}),
            'cod_charge': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '6', 'decimal_places': '2', 'blank': 'True'}),
            'condition': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '5', 'db_index': 'True'}),
            'gift_desc': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'gift_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_cod_available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_prefered': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'list_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'offer_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'payment_charges_paid_by': ('django.db.models.fields.CharField', [], {'default': "'chaupaati'", 'max_length': '15'}),
            'payment_collection_charges': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Product']"}),
            'seller': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products_offered'", 'to': "orm['accounts.Account']"}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'shipping_duration': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'shipping_paid_by': ('django.db.models.fields.CharField', [], {'default': "'vendor'", 'max_length': '15'}),
            'sku': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '25', 'db_index': 'True'}),
            'stock_status': ('django.db.models.fields.CharField', [], {'default': "'instock'", 'max_length': '100'}),
            'transfer_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'visibility_status': ('django.db.models.fields.CharField', [], {'default': "'always_visible'", 'max_length': '100', 'db_index': 'True'}),
            'warranty': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'whats_in_the_box': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'categories.category': {
            'Meta': {'object_name': 'Category'},
            'ext_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'moderate': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']", 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['categories.Store']", 'null': 'True', 'blank': 'True'})
        },
        'categories.store': {
            'Meta': {'object_name': 'Store'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locations.address': {
            'Meta': {'object_name': 'Address'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']", 'null': 'True'}),
            'address': ('django.db.models.fields.TextField', [], {}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']"}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'pincode': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'uses': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'locations.city': {
            'Meta': {'object_name': 'City'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']", 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': "'15'", 'db_index': 'True'}),
            'user_created': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'})
        },
        'locations.country': {
            'Meta': {'object_name': 'Country'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': "'15'", 'db_index': 'True'}),
            'user_created': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'})
        },
        'locations.state': {
            'Meta': {'object_name': 'State'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': "'15'", 'db_index': 'True'}),
            'user_created': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'})
        },
        'orders.billinginfo': {
            'Meta': {'object_name': 'BillingInfo'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Address']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Order']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'orders.deliveryinfo': {
            'Meta': {'object_name': 'DeliveryInfo'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Address']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Order']"})
        },
        'orders.giftinfo': {
            'Meta': {'object_name': 'GiftInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Order']"})
        },
        'orders.order': {
            'Meta': {'object_name': 'Order'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'agent_orders'", 'null': 'True', 'to': "orm['users.Profile']"}),
            'call_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['promotions.Coupon']", 'null': 'True', 'blank': 'True'}),
            'coupon_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_price_total': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'medium': ('django.db.models.fields.CharField', [], {'default': "'cc'", 'max_length': '5', 'blank': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'partner': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'payable_amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'payment_mode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '15', 'blank': 'True'}),
            'payment_realized_mode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '15', 'blank': 'True'}),
            'payment_realized_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reference_order_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'unassigned_cart'", 'max_length': '15'}),
            'taxes': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'transaction_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'blank': 'True'})
        },
        'orders.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'delivered_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dispatch_due_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dispatched_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gift_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'list_price': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Order']"}),
            'qty': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'sale_price': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'seller_rate_chart': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.SellerRateChart']", 'null': 'True', 'blank': 'True'}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'})
        },
        'orders.orderitems': {
            'Meta': {'object_name': 'OrderItems', 'db_table': "u'order_items'"},
            'billedamount': ('django.db.models.fields.FloatField', [], {'null': 'True', 'db_column': "'billedAmount'", 'blank': 'True'}),
            'coupondiscount': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'db_column': "'couponDiscount'", 'decimal_places': '2', 'max_digits': '27'}),
            'courierservicename': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'courierServiceName'", 'blank': 'True'}),
            'couriertrackingnumber': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'courierTrackingNumber'", 'blank': 'True'}),
            'courierurl': ('django.db.models.fields.CharField', [], {'max_length': '300', 'db_column': "'courierUrl'", 'blank': 'True'}),
            'deliverystatus': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'deliveryStatus'", 'blank': 'True'}),
            'discount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '27', 'decimal_places': '5', 'blank': 'True'}),
            'discountcode': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'discountCode'", 'blank': 'True'}),
            'discountsponsorid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_column': "'discountSponsorId'", 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'itemdata': ('django.db.models.fields.CharField', [], {'max_length': '3000', 'db_column': "'itemData'", 'blank': 'True'}),
            'itemid': ('django.db.models.fields.CharField', [], {'max_length': '300', 'db_column': "'itemId'", 'blank': 'True'}),
            'itemprice': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'db_column': "'itemPrice'", 'decimal_places': '5', 'max_digits': '27'}),
            'itemtype': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'itemType'"}),
            'modifiedon': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "'modifiedOn'", 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'orderid': ('django.db.models.fields.BigIntegerField', [], {'db_column': "'orderId'"}),
            'payableamount': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'db_column': "'payableAmount'", 'decimal_places': '5', 'max_digits': '27'}),
            'planid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_column': "'planId'", 'blank': 'True'}),
            'producttype': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'productType'", 'blank': 'True'}),
            'quantity': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'sellerid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_column': "'sellerId'", 'blank': 'True'}),
            'sequence': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'shippingcharges': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'db_column': "'shippingCharges'", 'decimal_places': '2', 'max_digits': '12'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'weight': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        },
        'orders.orders': {
            'Meta': {'object_name': 'Orders', 'db_table': "u'orders'"},
            'billedamount': ('django.db.models.fields.DecimalField', [], {'db_column': "'billedAmount'", 'decimal_places': '5', 'max_digits': '27'}),
            'billingaddress': ('django.db.models.fields.CharField', [], {'max_length': '1500', 'db_column': "'billingAddress'", 'blank': 'True'}),
            'billingcity': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'billingCity'", 'blank': 'True'}),
            'billingcountry': ('django.db.models.fields.CharField', [], {'max_length': '75', 'db_column': "'billingCountry'", 'blank': 'True'}),
            'billinglocality': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'billingLocality'", 'blank': 'True'}),
            'billingname': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'billingName'", 'blank': 'True'}),
            'billingphone': ('django.db.models.fields.CharField', [], {'max_length': '45', 'db_column': "'billingPhone'", 'blank': 'True'}),
            'billingpincode': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_column': "'billingPincode'", 'blank': 'True'}),
            'billingstate': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'billingState'", 'blank': 'True'}),
            'callid': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'callId'", 'blank': 'True'}),
            'coupondiscount': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'db_column': "'couponDiscount'", 'decimal_places': '2', 'max_digits': '27'}),
            'createdby': ('django.db.models.fields.CharField', [], {'max_length': '75', 'db_column': "'createdBy'", 'blank': 'True'}),
            'deliveryaddress': ('django.db.models.fields.CharField', [], {'max_length': '1500', 'db_column': "'deliveryAddress'", 'blank': 'True'}),
            'deliverycity': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'deliveryCity'", 'blank': 'True'}),
            'deliverycountry': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'deliveryCountry'", 'blank': 'True'}),
            'deliverydate': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "'deliveryDate'", 'blank': 'True'}),
            'deliverygiftnotes': ('django.db.models.fields.CharField', [], {'max_length': '1500', 'db_column': "'deliveryGiftNotes'", 'blank': 'True'}),
            'deliverylocality': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'deliveryLocality'", 'blank': 'True'}),
            'deliveryname': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'deliveryName'", 'blank': 'True'}),
            'deliverynotes': ('django.db.models.fields.CharField', [], {'max_length': '1500', 'db_column': "'deliveryNotes'", 'blank': 'True'}),
            'deliveryphone': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'deliveryPhone'", 'blank': 'True'}),
            'deliverypincode': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_column': "'deliveryPincode'", 'blank': 'True'}),
            'deliverystate': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'deliveryState'", 'blank': 'True'}),
            'discount': ('django.db.models.fields.DecimalField', [], {'max_digits': '27', 'decimal_places': '5'}),
            'discountcode': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'discountCode'", 'blank': 'True'}),
            'discountsponsorid': ('django.db.models.fields.BigIntegerField', [], {'null': 'True', 'db_column': "'discountSponsorId'", 'blank': 'True'}),
            'expireson': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "'expiresOn'", 'blank': 'True'}),
            'friendlyorderid': ('django.db.models.fields.CharField', [], {'max_length': '150', 'db_column': "'friendlyOrderId'", 'blank': 'True'}),
            'fulfilledon': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "'fulfilledOn'", 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'modifiedon': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "'modifiedOn'", 'blank': 'True'}),
            'payableamount': ('django.db.models.fields.DecimalField', [], {'db_column': "'payableAmount'", 'decimal_places': '5', 'max_digits': '27'}),
            'paymentmode': ('django.db.models.fields.CharField', [], {'max_length': '90', 'db_column': "'paymentMode'", 'blank': 'True'}),
            'paymentrealizedmode': ('django.db.models.fields.CharField', [], {'max_length': '90', 'db_column': "'paymentRealizedMode'", 'blank': 'True'}),
            'paymentrealizedon': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_column': "'paymentRealizedOn'", 'blank': 'True'}),
            'process': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'shippingcharges': ('django.db.models.fields.DecimalField', [], {'blank': 'True', 'null': 'True', 'db_column': "'shippingCharges'", 'decimal_places': '2', 'max_digits': '12'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateField', [], {}),
            'userid': ('django.db.models.fields.BigIntegerField', [], {'db_column': "'userId'"})
        },
        'orders.shippingdetails': {
            'Meta': {'object_name': 'ShippingDetails'},
            'courier': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'order_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.OrderItem']"}),
            'tracking_no': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'tracking_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'orders.subscriptiondetails': {
            'Meta': {'object_name': 'SubscriptionDetails'},
            'ends_on': ('django.db.models.fields.DateField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'no_issues': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'order_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.OrderItem']"}),
            'starts_from': ('django.db.models.fields.DateField', [], {'blank': 'True'}),
            'subscription_no': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'promotions.coupon': {
            'Meta': {'object_name': 'Coupon'},
            'applies_to': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'discount_type': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'discount_value': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'expires_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'given_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_uses': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'inactive'", 'max_length': '25'}),
            'use_when': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '25'}),
            'uses': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'users.profile': {
            'Meta': {'object_name': 'Profile'},
            'acquired_through_account': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_customers'", 'null': 'True', 'to': "orm['accounts.Account']"}),
            'buyer_or_seller': ('django.db.models.fields.CharField', [], {'default': "'Buyer'", 'max_length': '100'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'customer_of_accounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'customers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['accounts.Account']"}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'managed_accounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'account_staff'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['accounts.Account']"}),
            'marketing_alerts': ('django.db.models.fields.CharField', [], {'default': "'neutral'", 'max_length': '25'}),
            'passcode': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'primary_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'primary_phone': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '15'}),
            'salt': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'salutation': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'secondary_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'secondary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['users.UserTag']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'users.usertag': {
            'Meta': {'object_name': 'UserTag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        }
    }

    complete_apps = ['orders']
