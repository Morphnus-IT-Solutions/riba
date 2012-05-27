# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'ProductGroup.threshold_amount'
        db.alter_column('fulfillment_productgroup', 'threshold_amount', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True))

        # Changing field 'LspZipgroup.lsp_priority'
        db.alter_column('fulfillment_lspzipgroup', 'lsp_priority', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=1, null=True, blank=True))

        # Adding field 'PincodeZipgroupMap.supported_product_groups'
        db.add_column('fulfillment_pincodezipgroupmap', 'supported_product_groups', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Changing field 'ProductGroup.threshold_amount'
        db.alter_column('fulfillment_productgroup', 'threshold_amount', self.gf('django.db.models.fields.PositiveIntegerField')())

        # Changing field 'LspZipgroup.lsp_priority'
        db.alter_column('fulfillment_lspzipgroup', 'lsp_priority', self.gf('django.db.models.fields.PositiveIntegerField')(max_length=1))

        # Deleting field 'PincodeZipgroupMap.supported_product_groups'
        db.delete_column('fulfillment_pincodezipgroupmap', 'supported_product_groups')


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
            'lsp_priority': ('django.db.models.fields.PositiveIntegerField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'zipgroup_code': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'zipgroup_name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'fulfillment.pincodezipgroupmap': {
            'Meta': {'unique_together': "(('zipgroup', 'pincode'),)", 'object_name': 'PincodeZipgroupMap'},
            'cod_flag': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'high_value': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pincode': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'supported_product_groups': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
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
            'threshold_amount': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['fulfillment']
