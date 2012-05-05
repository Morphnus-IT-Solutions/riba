# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'Feedback', fields ['phone']
        db.delete_unique('feedback_feedback', ['phone'])

        # Changing field 'Feedback.email'
        db.alter_column('feedback_feedback', 'email', self.gf('django.db.models.fields.EmailField')(max_length=75))


    def backwards(self, orm):
        
        # Adding unique constraint on 'Feedback', fields ['phone']
        db.create_unique('feedback_feedback', ['phone'])

        # Changing field 'Feedback.email'
        db.alter_column('feedback_feedback', 'email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True))


    models = {
        'accounts.client': {
            'Meta': {'object_name': 'Client'},
            'confirmed_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> order@chaupaati.com'", 'max_length': '500'}),
            'confirmed_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'pending_order_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> lead@chaupaati.com'", 'max_length': '500'}),
            'pending_order_helpline': ('django.db.models.fields.CharField', [], {'default': "'0-922-222-1947'", 'max_length': '25'}),
            'share_product_email': ('django.db.models.fields.CharField', [], {'default': "'<Chaupaati Bazaar> share@chaupaati.com'", 'max_length': '500'}),
            'signature': ('django.db.models.fields.TextField', [], {}),
            'sms_mask': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'feedback.feedback': {
            'Meta': {'object_name': 'Feedback'},
            'client': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Client']", 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'feedback': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        }
    }

    complete_apps = ['feedback']
