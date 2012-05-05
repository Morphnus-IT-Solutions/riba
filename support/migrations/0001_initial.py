# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Team'
        db.create_table('support_team', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
        ))
        db.send_create_signal('support', ['Team'])

        # Adding model 'User'
        db.create_table('support_user', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', unique=True, to=orm['auth.User'])),
            ('team', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='members', null=True, to=orm['support.Team'])),
            ('role', self.gf('django.db.models.fields.CharField')(default='member', max_length=10)),
        ))
        db.send_create_signal('support', ['User'])

        # Adding unique constraint on 'User', fields ['user', 'team']
        db.create_unique('support_user', ['user_id', 'team_id'])

        # Adding model 'State'
        db.create_table('support_state', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('responsible_team', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='responsible_states', null=True, to=orm['support.Team'])),
        ))
        db.send_create_signal('support', ['State'])

        # Adding model 'SubState'
        db.create_table('support_substate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='substates', to=orm['support.State'])),
            ('acting_team', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='acting_substates', null=True, to=orm['support.Team'])),
            ('tat', self.gf('utils.fields.TimeDeltaField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('support', ['SubState'])

        # Adding unique constraint on 'SubState', fields ['name', 'state']
        db.create_unique('support_substate', ['name', 'state_id'])

        # Adding model 'ActionFlow'
        db.create_table('support_actionflow', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('initial_state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['support.State'])),
            ('initial_substate', self.gf('django.db.models.fields.related.ForeignKey')(related_name='out_action_flows', to=orm['support.SubState'])),
            ('final_state', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['support.State'])),
            ('final_substate', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='in_action_flows', null=True, to=orm['support.SubState'])),
        ))
        db.send_create_signal('support', ['ActionFlow'])

        # Adding unique constraint on 'ActionFlow', fields ['name', 'initial_substate', 'final_substate']
        db.create_unique('support_actionflow', ['name', 'initial_substate_id', 'final_substate_id'])

        # Adding model 'InformationFlow'
        db.create_table('support_informationflow', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('substate', self.gf('django.db.models.fields.related.ForeignKey')(related_name='information_flows', to=orm['support.SubState'])),
            ('acting_team', self.gf('django.db.models.fields.related.ForeignKey')(related_name='information_flows', to=orm['support.Team'])),
        ))
        db.send_create_signal('support', ['InformationFlow'])

        # Adding unique constraint on 'InformationFlow', fields ['name', 'substate']
        db.create_unique('support_informationflow', ['name', 'substate_id'])

        # Adding M2M table for field receipients on 'InformationFlow'
        db.create_table('support_informationflow_receipients', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('informationflow', models.ForeignKey(orm['support.informationflow'], null=False)),
            ('team', models.ForeignKey(orm['support.team'], null=False))
        ))
        db.create_unique('support_informationflow_receipients', ['informationflow_id', 'team_id'])

        # Adding model 'OrderStatus'
        db.create_table('support_orderstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.OneToOneField')(related_name='order_status', unique=True, to=orm['orders.Order'])),
            ('state', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='orders', null=True, to=orm['support.State'])),
            ('substate', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='orders', null=True, to=orm['support.SubState'])),
            ('last_action', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['support.Action'])),
            ('last_acted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['support.User'])),
            ('last_acted_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_shifted_on', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('on_hold', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('support', ['OrderStatus'])

        # Adding model 'Action'
        db.create_table('support_action', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['support.User'])),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['support.OrderStatus'])),
            ('order_item', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='+', null=True, to=orm['orders.OrderItem'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True, blank=True)),
            ('flow_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['contenttypes.ContentType'])),
            ('flow_object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('support', ['Action'])

        # Adding model 'Escalation'
        db.create_table('support_escalation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(related_name='escalations', to=orm['support.OrderStatus'])),
            ('state', self.gf('django.db.models.fields.related.ForeignKey')(related_name='escalations', to=orm['support.State'])),
            ('substate', self.gf('django.db.models.fields.related.ForeignKey')(related_name='escalations', to=orm['support.SubState'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('support', ['Escalation'])


    def backwards(self, orm):
        
        # Deleting model 'Team'
        db.delete_table('support_team')

        # Deleting model 'User'
        db.delete_table('support_user')

        # Removing unique constraint on 'User', fields ['user', 'team']
        db.delete_unique('support_user', ['user_id', 'team_id'])

        # Deleting model 'State'
        db.delete_table('support_state')

        # Deleting model 'SubState'
        db.delete_table('support_substate')

        # Removing unique constraint on 'SubState', fields ['name', 'state']
        db.delete_unique('support_substate', ['name', 'state_id'])

        # Deleting model 'ActionFlow'
        db.delete_table('support_actionflow')

        # Removing unique constraint on 'ActionFlow', fields ['name', 'initial_substate', 'final_substate']
        db.delete_unique('support_actionflow', ['name', 'initial_substate_id', 'final_substate_id'])

        # Deleting model 'InformationFlow'
        db.delete_table('support_informationflow')

        # Removing unique constraint on 'InformationFlow', fields ['name', 'substate']
        db.delete_unique('support_informationflow', ['name', 'substate_id'])

        # Removing M2M table for field receipients on 'InformationFlow'
        db.delete_table('support_informationflow_receipients')

        # Deleting model 'OrderStatus'
        db.delete_table('support_orderstatus')

        # Deleting model 'Action'
        db.delete_table('support_action')

        # Deleting model 'Escalation'
        db.delete_table('support_escalation')


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
        'affiliates.affiliate': {
            'Meta': {'object_name': 'Affiliate'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_coupon_avail': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'})
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
        'categories.producttype': {
            'Meta': {'object_name': 'ProductType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
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
        'orders.order': {
            'Meta': {'object_name': 'Order'},
            'agent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'agent_orders'", 'null': 'True', 'to': "orm['users.Profile']"}),
            'auto_promotions_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'call_id': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50', 'blank': 'True'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['promotions.Coupon']", 'null': 'True', 'blank': 'True'}),
            'coupon_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'ga_tracked': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'list_price_total': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'medium': ('django.db.models.fields.CharField', [], {'default': "'cc'", 'max_length': '5', 'blank': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'blank': 'True'}),
            'partner': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'payable_amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'payback_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'payment_mode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '25', 'blank': 'True'}),
            'payment_realized_mode': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '25', 'blank': 'True'}),
            'payment_realized_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reference_order_id': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '10', 'blank': 'True'}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'unassigned_cart'", 'max_length': '15'}),
            'taxes': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'top10_discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '22', 'decimal_places': '2', 'blank': 'True'}),
            'total': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'transaction_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.Profile']", 'null': 'True', 'blank': 'True'}),
            'verify_code': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'wstore': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']", 'null': 'True', 'blank': 'True'})
        },
        'orders.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'delivered_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dispatch_due_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'dispatched_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'gift_title': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_title': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'list_price': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'offer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['promotions.Offer']", 'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['orders.Order']"}),
            'qty': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'sale_price': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'seller_rate_chart': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['catalog.SellerRateChart']", 'null': 'True', 'blank': 'True'}),
            'shipping_charges': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '22', 'decimal_places': '2'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'promotions.coupon': {
            'Meta': {'unique_together': "(('code', 'status'),)", 'object_name': 'Coupon'},
            'affiliate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['affiliates.Affiliate']", 'null': 'True', 'blank': 'True'}),
            'applicable_on': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['catalog.SellerRateChart']", 'null': 'True', 'blank': 'True'}),
            'applies_to': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
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
        'support.action': {
            'Meta': {'object_name': 'Action'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'flow_object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'flow_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['support.OrderStatus']"}),
            'order_item': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['orders.OrderItem']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['support.User']"})
        },
        'support.actionflow': {
            'Meta': {'unique_together': "(('name', 'initial_substate', 'final_substate'),)", 'object_name': 'ActionFlow'},
            'final_state': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['support.State']"}),
            'final_substate': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'in_action_flows'", 'null': 'True', 'to': "orm['support.SubState']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'initial_state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['support.State']"}),
            'initial_substate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'out_action_flows'", 'to': "orm['support.SubState']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'support.escalation': {
            'Meta': {'object_name': 'Escalation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'escalations'", 'to': "orm['support.OrderStatus']"}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'escalations'", 'to': "orm['support.State']"}),
            'substate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'escalations'", 'to': "orm['support.SubState']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        },
        'support.informationflow': {
            'Meta': {'unique_together': "(('name', 'substate'),)", 'object_name': 'InformationFlow'},
            'acting_team': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'information_flows'", 'to': "orm['support.Team']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'receipients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'+'", 'symmetrical': 'False', 'to': "orm['support.Team']"}),
            'substate': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'information_flows'", 'to': "orm['support.SubState']"})
        },
        'support.orderstatus': {
            'Meta': {'object_name': 'OrderStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_acted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['support.User']"}),
            'last_acted_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_action': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'+'", 'null': 'True', 'to': "orm['support.Action']"}),
            'last_shifted_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'on_hold': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'order': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'order_status'", 'unique': 'True', 'to': "orm['orders.Order']"}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'orders'", 'null': 'True', 'to': "orm['support.State']"}),
            'substate': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'orders'", 'null': 'True', 'to': "orm['support.SubState']"})
        },
        'support.state': {
            'Meta': {'object_name': 'State'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'responsible_team': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'responsible_states'", 'null': 'True', 'to': "orm['support.Team']"})
        },
        'support.substate': {
            'Meta': {'unique_together': "(('name', 'state'),)", 'object_name': 'SubState'},
            'acting_team': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'acting_substates'", 'null': 'True', 'to': "orm['support.Team']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'substates'", 'to': "orm['support.State']"}),
            'tat': ('utils.fields.TimeDeltaField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'support.team': {
            'Meta': {'object_name': 'Team'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'})
        },
        'support.user': {
            'Meta': {'unique_together': "(('user', 'team'),)", 'object_name': 'User'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'default': "'member'", 'max_length': '10'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'members'", 'null': 'True', 'to': "orm['support.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'unique': 'True', 'to': "orm['auth.User']"})
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
            'atg_username': ('django.db.models.fields.CharField', [], {'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'buyer_or_seller': ('django.db.models.fields.CharField', [], {'default': "'Buyer'", 'max_length': '100'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'customer_of_accounts': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'customers'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['accounts.Account']"}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'email_notification': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'facebook': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'default': "'m'", 'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_agent': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
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
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user_photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
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

    complete_apps = ['support']
