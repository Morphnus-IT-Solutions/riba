# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Lsp'
        db.create_table('fulfillment_lsp', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=6)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=15)),
        ))
        db.send_create_signal('fulfillment', ['Lsp'])

        # Adding model 'ProductGroup'
        db.create_table('fulfillment_productgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'])),
            ('local_tag', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('ship_mode', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('high_value_flag', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('threshold_amount', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('fulfillment', ['ProductGroup'])

        # Adding unique constraint on 'ProductGroup', fields ['name', 'client']
        db.create_unique('fulfillment_productgroup', ['name', 'client_id'])

        # Adding model 'Dc'
        db.create_table('fulfillment_dc', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=6)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('cod_flag', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('client', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Client'])),
            ('address', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
        ))
        db.send_create_signal('fulfillment', ['Dc'])

        # Adding unique constraint on 'Dc', fields ['code', 'client']
        db.create_unique('fulfillment_dc', ['code', 'client_id'])

        # Adding model 'LspZipgroup'
        db.create_table('fulfillment_lspzipgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lsp', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fulfillment.Lsp'])),
            ('zipgroup_name', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('zipgroup_code', self.gf('django.db.models.fields.CharField')(max_length=3)),
            ('lsp_priority', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=1)),
        ))
        db.send_create_signal('fulfillment', ['LspZipgroup'])

        # Adding unique constraint on 'LspZipgroup', fields ['zipgroup_name', 'lsp']
        db.create_unique('fulfillment_lspzipgroup', ['zipgroup_name', 'lsp_id'])

        # Adding model 'LspProductGroup'
        db.create_table('fulfillment_lspproductgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product_group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fulfillment.ProductGroup'])),
            ('lsp', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fulfillment.Lsp'])),
        ))
        db.send_create_signal('fulfillment', ['LspProductGroup'])

        # Adding unique constraint on 'LspProductGroup', fields ['lsp', 'product_group']
        db.create_unique('fulfillment_lspproductgroup', ['lsp_id', 'product_group_id'])

        # Adding model 'DcZipgroup'
        db.create_table('fulfillment_dczipgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fulfillment.Dc'])),
            ('zipgroup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fulfillment.LspZipgroup'])),
        ))
        db.send_create_signal('fulfillment', ['DcZipgroup'])

        # Adding unique constraint on 'DcZipgroup', fields ['zipgroup', 'dc']
        db.create_unique('fulfillment_dczipgroup', ['zipgroup_id', 'dc_id'])

        # Adding model 'PincodeZipgroupMap'
        db.create_table('fulfillment_pincodezipgroupmap', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('zipgroup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fulfillment.LspZipgroup'])),
            ('pincode', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('cod_flag', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('high_value', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('fulfillment', ['PincodeZipgroupMap'])

        # Adding unique constraint on 'PincodeZipgroupMap', fields ['zipgroup', 'pincode']
        db.create_unique('fulfillment_pincodezipgroupmap', ['zipgroup_id', 'pincode'])

        # Adding model 'LspDeliveryChart'
        db.create_table('fulfillment_lspdeliverychart', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fulfillment.Dc'])),
            ('zipgroup', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['fulfillment.LspZipgroup'])),
            ('transit_time', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('ship_mode', self.gf('django.db.models.fields.CharField')(max_length=8)),
        ))
        db.send_create_signal('fulfillment', ['LspDeliveryChart'])


    def backwards(self, orm):
        
        # Deleting model 'Lsp'
        db.delete_table('fulfillment_lsp')

        # Deleting model 'ProductGroup'
        db.delete_table('fulfillment_productgroup')

        # Removing unique constraint on 'ProductGroup', fields ['name', 'client']
        db.delete_unique('fulfillment_productgroup', ['name', 'client_id'])

        # Deleting model 'Dc'
        db.delete_table('fulfillment_dc')

        # Removing unique constraint on 'Dc', fields ['code', 'client']
        db.delete_unique('fulfillment_dc', ['code', 'client_id'])

        # Deleting model 'LspZipgroup'
        db.delete_table('fulfillment_lspzipgroup')

        # Removing unique constraint on 'LspZipgroup', fields ['zipgroup_name', 'lsp']
        db.delete_unique('fulfillment_lspzipgroup', ['zipgroup_name', 'lsp_id'])

        # Deleting model 'LspProductGroup'
        db.delete_table('fulfillment_lspproductgroup')

        # Removing unique constraint on 'LspProductGroup', fields ['lsp', 'product_group']
        db.delete_unique('fulfillment_lspproductgroup', ['lsp_id', 'product_group_id'])

        # Deleting model 'DcZipgroup'
        db.delete_table('fulfillment_dczipgroup')

        # Removing unique constraint on 'DcZipgroup', fields ['zipgroup', 'dc']
        db.delete_unique('fulfillment_dczipgroup', ['zipgroup_id', 'dc_id'])

        # Deleting model 'PincodeZipgroupMap'
        db.delete_table('fulfillment_pincodezipgroupmap')

        # Removing unique constraint on 'PincodeZipgroupMap', fields ['zipgroup', 'pincode']
        db.delete_unique('fulfillment_pincodezipgroupmap', ['zipgroup_id', 'pincode'])

        # Deleting model 'LspDeliveryChart'
        db.delete_table('fulfillment_lspdeliverychart')


    models = {
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
        'fulfillment.dc': {
            'Meta': {'unique_together': "(('code', 'client'),)", 'object_name': 'Dc'},
            'address': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'cod_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '6'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'fulfillment.dczipgroup': {
            'Meta': {'unique_together': "(('zipgroup', 'dc'),)", 'object_name': 'DcZipgroup'},
            'dc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fulfillment.Dc']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'zipgroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fulfillment.LspZipgroup']"})
        },
        'fulfillment.lsp': {
            'Meta': {'object_name': 'Lsp'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '6'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '15'})
        },
        'fulfillment.lspdeliverychart': {
            'Meta': {'object_name': 'LspDeliveryChart'},
            'dc': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fulfillment.Dc']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ship_mode': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'transit_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'zipgroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fulfillment.LspZipgroup']"})
        },
        'fulfillment.lspproductgroup': {
            'Meta': {'unique_together': "(('lsp', 'product_group'),)", 'object_name': 'LspProductGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lsp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fulfillment.Lsp']"}),
            'product_group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fulfillment.ProductGroup']"})
        },
        'fulfillment.lspzipgroup': {
            'Meta': {'unique_together': "(('zipgroup_name', 'lsp'),)", 'object_name': 'LspZipgroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lsp': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fulfillment.Lsp']"}),
            'lsp_priority': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '1'}),
            'zipgroup_code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'zipgroup_name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'fulfillment.pincodezipgroupmap': {
            'Meta': {'unique_together': "(('zipgroup', 'pincode'),)", 'object_name': 'PincodeZipgroupMap'},
            'cod_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'high_value': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pincode': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'zipgroup': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['fulfillment.LspZipgroup']"})
        },
        'fulfillment.productgroup': {
            'Meta': {'unique_together': "(('name', 'client'),)", 'object_name': 'ProductGroup'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']"}),
            'high_value_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'local_tag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'ship_mode': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'threshold_amount': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['fulfillment']
