# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'CancelledOrderItem'
        #db.delete_table('orders_cancelledorderitem')

        # Deleting model 'SubscriptionDetails'
        db.delete_table('orders_subscriptiondetails')

        # Deleting model 'BundleItem'
        db.delete_table('orders_bundleitem')

        # Deleting model 'BulkOrderDetails'
        db.delete_table('orders_bulkorderdetails')

        # Deleting model 'ThirdPartyOrders'
        db.delete_table('orders_thirdpartyorders')

        # Deleting model 'CodOrderVerification'
        db.delete_table('orders_codorderverification')

        # Deleting model 'OrderXML'
        db.delete_table('orders_orderxml')

        # Deleting field 'Order.booking_agent'
        db.delete_column('orders_order', 'booking_agent_id')

        # Deleting field 'Order.agent'
        db.delete_column('orders_order', 'agent_id')

        # Deleting field 'Order.payment_mode'
        db.delete_column('orders_order', 'payment_mode')

        # Deleting field 'Order.partner'
        db.delete_column('orders_order', 'partner')

        # Deleting field 'Order.wstore'
        db.delete_column('orders_order', 'wstore_id')

        # Deleting field 'Order.confirming_agent'
        db.delete_column('orders_order', 'confirming_agent_id')

        # Deleting field 'Order.payback_id'
        #db.delete_column('orders_order', 'payback_id')

        # Deleting field 'Order.reference_order_id'
        db.delete_column('orders_order', 'reference_order_id')

        # Deleting field 'Order.call_id'
        db.delete_column('orders_order', 'call_id')

        # Deleting field 'Order.ga_tracked'
        db.delete_column('orders_order', 'ga_tracked')

        # Deleting field 'Order.sap_date'
        db.delete_column('orders_order', 'sap_date')


    def backwards(self, orm):
        
        # Adding model 'CancelledOrderItem'
        db.create_table('orders_cancelledorderitem', (
            ('cancellation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('refundable_amount', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=22, decimal_places=2)),
            ('refund_status', self.gf('django.db.models.fields.CharField')(default='pending', max_length=100)),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['orders.OrderItem'])),
        ))
        db.send_create_signal('orders', ['CancelledOrderItem'])

        # Adding model 'SubscriptionDetails'
        db.create_table('orders_subscriptiondetails', (
            ('ends_on', self.gf('django.db.models.fields.DateField')(blank=True)),
            ('subscription_no', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('no_issues', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('order_item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['orders.OrderItem'])),
            ('notes', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('starts_from', self.gf('django.db.models.fields.DateField')(blank=True)),
        ))
        db.send_create_signal('orders', ['SubscriptionDetails'])

        # Adding model 'BundleItem'
        db.create_table('orders_bundleitem', (
            ('bundle_item', self.gf('django.db.models.fields.related.OneToOneField')(related_name='bundle_item', unique=True, to=orm['orders.OrderItem'])),
            ('qty', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('parent_item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['orders.OrderItem'])),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['orders.Order'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('orders', ['BundleItem'])

        # Adding model 'BulkOrderDetails'
        db.create_table('orders_bulkorderdetails', (
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=11)),
            ('requirement', self.gf('django.db.models.fields.TextField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('submitted_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('organization', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('orders', ['BulkOrderDetails'])

        # Adding model 'ThirdPartyOrders'
        db.create_table('orders_thirdpartyorders', (
            ('third_party_order', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('bp_number', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['orders.Order'])),
            ('receipt_no', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('orders', ['ThirdPartyOrders'])

        # Adding model 'CodOrderVerification'
        db.create_table('orders_codorderverification', (
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True, db_index=True)),
            ('mobile_no', self.gf('django.db.models.fields.CharField')(default='', max_length=15, null=True, blank=True)),
            ('reference_order_id', self.gf('django.db.models.fields.CharField')(blank=True, max_length=15, null=True, db_index=True)),
            ('verification_code', self.gf('django.db.models.fields.CharField')(blank=True, max_length=50, null=True, db_index=True)),
            ('verified_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('is_verified', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['orders.Order'])),
        ))
        db.send_create_signal('orders', ['CodOrderVerification'])

        # Adding model 'OrderXML'
        db.create_table('orders_orderxml', (
            ('status', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('reference_order_id', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('attempts', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('modified_on', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('xml', self.gf('django.db.models.fields.TextField')()),
            ('expiry_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('error_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('reason', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['orders.Order'])),
        ))
        db.send_create_signal('orders', ['OrderXML'])

        # Adding field 'Order.booking_agent'
        db.add_column('orders_order', 'booking_agent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='booking_agent_orders', null=True, to=orm['users.Profile'], blank=True), keep_default=False)

        # Adding field 'Order.agent'
        db.add_column('orders_order', 'agent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='agent_orders', null=True, to=orm['users.Profile'], blank=True), keep_default=False)

        # Adding field 'Order.payment_mode'
        db.add_column('orders_order', 'payment_mode', self.gf('django.db.models.fields.CharField')(default='', max_length=25, blank=True), keep_default=False)

        # Adding field 'Order.partner'
        db.add_column('orders_order', 'partner', self.gf('django.db.models.fields.CharField')(default='', max_length=100, blank=True), keep_default=False)

        # Adding field 'Order.wstore'
        db.add_column('orders_order', 'wstore', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Account'], null=True, blank=True), keep_default=False)

        # Adding field 'Order.confirming_agent'
        db.add_column('orders_order', 'confirming_agent', self.gf('django.db.models.fields.related.ForeignKey')(related_name='confirming_agent_orders', null=True, to=orm['users.Profile'], blank=True), keep_default=False)

        # Adding field 'Order.payback_id'
        db.add_column('orders_order', 'payback_id', self.gf('django.db.models.fields.CharField')(blank=True, max_length=16, null=True, db_index=True), keep_default=False)

        # Adding field 'Order.reference_order_id'
        db.add_column('orders_order', 'reference_order_id', self.gf('django.db.models.fields.CharField')(blank=True, default='', max_length=15, db_index=True), keep_default=False)

        # Adding field 'Order.call_id'
        db.add_column('orders_order', 'call_id', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True), keep_default=False)

        # Adding field 'Order.ga_tracked'
        db.add_column('orders_order', 'ga_tracked', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Adding field 'Order.sap_date'
        db.add_column('orders_order', 'sap_date', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True), keep_default=False)


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
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
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
            'is_online': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
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
            'is_bundle': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_cod_available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_fmemi_available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_free_shipping': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_prefered': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_so_available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'key_feature': ('tinymce.models.HTMLField', [], {'null': 'True', 'blank': 'True'}),
            'list_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'max_shipping': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'min_qty': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'min_shipping': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'offer_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2'}),
            'otc': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'payment_charges_paid_by': ('django.db.models.fields.CharField', [], {'default': "'chaupaati'", 'max_length': '15'}),
            'payment_collection_charges': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'pricing_maintained': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '100'}),
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '100', 'db_index': 'True'}),
            'tagline': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'})
        },
        'categories.producttype': {
            'Meta': {'unique_together': "(('type', 'client'),)", 'object_name': 'ProductType'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
            'address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']", 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']", 'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'defaddress': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'pincode': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'uses': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'locations.city': {
            'Meta': {'object_name': 'City'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']", 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']", 'null': 'True', 'blank': 'True'}),
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
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'billing_info'", 'unique': 'True', 'null': 'True', 'to': "orm['orders.Order']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'blank': 'True'})
        },
        'orders.cancelledorder': {
            'Meta': {'object_name': 'CancelledOrder'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Order']"}),
            'refund_amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']"})
        },
        'orders.deliveryinfo': {
            'Meta': {'object_name': 'DeliveryInfo'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Address']"}),
            'gift_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'delivery_info'", 'unique': 'True', 'to': "orm['orders.Order']"})
        },
        'orders.giftinfo': {
            'Meta': {'object_name': 'GiftInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Order']"})
        },
        'orders.order': {
            'Meta': {'object_name': 'Order'},
            'auto_promotions_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'booking_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'cashback_amount_total': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'client_domain': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['accounts.ClientDomain']", 'null': 'True', 'blank': 'True'}),
            'confirming_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['promotions.Coupon']", 'null': 'True', 'blank': 'True'}),
            'coupon_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_price_total': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'medium': ('django.db.models.fields.CharField', [], {'default': "'cc'", 'max_length': '20', 'blank': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'payable_amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'payment_realized_mode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '25', 'blank': 'True'}),
            'payment_realized_on': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'unassigned_cart'", 'max_length': '25', 'db_index': 'True'}),
            'support_state': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'taxes': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'top10_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'transaction_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'blank': 'True'}),
            'verify_code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'orders.ordercount': {
            'Meta': {'object_name': 'OrderCount'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_count': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '8', 'decimal_places': '0', 'db_index': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Product']"})
        },
        'orders.ordercountbystate': {
            'Meta': {'object_name': 'OrderCountByState'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_count': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '8', 'decimal_places': '0'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Product']"}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'pending_order'", 'max_length': '20', 'db_index': 'True'})
        },
        'orders.orderdailycount': {
            'Meta': {'object_name': 'OrderDailyCount'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']", 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order_count': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '8', 'decimal_places': '0'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.Product']"})
        },
        'orders.orderhistory': {
            'Meta': {'object_name': 'OrderHistory'},
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['promotions.Coupon']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Order']"}),
            'payable_amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'blank': 'True'})
        },
        'orders.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'cashback_amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'delivery_days': ('django.db.models.fields.IntegerField', [], {'default': "'0'", 'null': 'True', 'blank': 'True'}),
            'discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'expected_delivery_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'expected_stock_arrival': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gift_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_inventory_blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'item_title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'list_price': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'offer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['promotions.Offer']", 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Order']"}),
            'qty': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'sale_price': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'seller_rate_chart': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.SellerRateChart']", 'null': 'True', 'blank': 'True'}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'total_amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'})
        },
        'orders.orderitemhistory': {
            'Meta': {'object_name': 'OrderItemHistory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'offer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['promotions.Offer']", 'null': 'True', 'blank': 'True'}),
            'order_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.OrderItem']"}),
            'qty': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'updated_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'blank': 'True'})
        },
        'orders.orderitemlog': {
            'Meta': {'object_name': 'OrderItemLog'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'expected_delivery_date': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'expected_stock_arrival': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'order_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'item_log'", 'to': "orm['orders.OrderItem']"}),
            'order_log': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'item_log'", 'to': "orm['orders.OrderLog']"}),
            'po_date': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'po_number': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'qty_new': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'qty_old': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'orders.orderlog': {
            'Meta': {'object_name': 'OrderLog'},
            'action': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'address_new': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'address_old': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'auto_promotions_discount_new': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'auto_promotions_discount_old': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'burn_points': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'coupon_new': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'+'", 'null': 'True', 'blank': 'True', 'to': "orm['promotions.Coupon']"}),
            'coupon_old': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'+'", 'null': 'True', 'blank': 'True', 'to': "orm['promotions.Coupon']"}),
            'discount_new': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'discount_old': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'earn_points': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'order_log'", 'to': "orm['orders.Order']"}),
            'payable_amount': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'payment_mode_new': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'payment_mode_old': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'+'", 'null': 'True', 'blank': 'True', 'to': "orm['users.Profile']"}),
            'shipping_charges_new': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'shipping_charges_old': ('django.db.models.fields.DecimalField', [], {'default': 'None', 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'orders.shippingdetails': {
            'Meta': {'object_name': 'ShippingDetails'},
            'courier': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'order_item': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.OrderItem']"}),
            'shipper_status': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'processing'", 'max_length': '100'}),
            'tracking_no': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'tracking_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'promotions.coupon': {
            'Meta': {'unique_together': "(('code', 'status'),)", 'object_name': 'Coupon'},
            'applicable_on': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['catalog.SellerRateChart']", 'null': 'True', 'blank': 'True'}),
            'applies_to': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'discount_available_on': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'discount_type': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'discount_value': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'expires_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'given_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_uses': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'newsletter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.NewsLetter']", 'null': 'True', 'blank': 'True'}),
            'promo_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'inactive'", 'max_length': '25'}),
            'use_when': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '25'}),
            'uses': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'promotions.offer': {
            'Meta': {'object_name': 'Offer'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'ends_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'price_label': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'stackable': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '25'}),
            'starts_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'draft'", 'max_length': '25'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        'users.newsletter': {
            'Meta': {'object_name': 'NewsLetter'},
            'affiliate_logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'affiliate_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'affiliate_text': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'client': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['accounts.Client']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsletter': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'users.profile': {
            'Meta': {'object_name': 'Profile'},
            'acquired_through_account': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_customers'", 'null': 'True', 'to': "orm['accounts.Account']"}),
            'atg_login': ('django.db.models.fields.CharField', [], {'max_length': '40', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'atg_password': ('django.db.models.fields.CharField', [], {'max_length': '35', 'null': 'True', 'blank': 'True'}),
            'atg_username': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'buyer_or_seller': ('django.db.models.fields.CharField', [], {'default': "'Buyer'", 'max_length': '100'}),
            'cod_status': ('django.db.models.fields.CharField', [], {'default': "'neutral'", 'max_length': '25'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'customer_of_accounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'customers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['accounts.Account']"}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'email_notification': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_agent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'managed_accounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'account_staff'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['accounts.Account']"}),
            'marketing_alerts': ('django.db.models.fields.CharField', [], {'default': "'neutral'", 'max_length': '25'}),
            'passcode': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'primary_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'primary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'profession': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'salt': ('django.db.models.fields.CharField', [], {'max_length': '36', 'blank': 'True'}),
            'salutation': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'secondary_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'secondary_phone': ('django.db.models.fields.CharField', [], {'max_length': '15', 'blank': 'True'}),
            'sms_alert': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['users.UserTag']", 'null': 'True', 'blank': 'True'}),
            'transaction_password': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user_photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'verification_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'verify_code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'webpage': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        'users.usertag': {
            'Meta': {'object_name': 'UserTag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        }
    }

    complete_apps = ['orders']
