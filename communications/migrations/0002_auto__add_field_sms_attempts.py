# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'SMS.attempts'
        db.add_column('communications_sms', 'attempts', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'SMS.attempts'
        db.delete_column('communications_sms', 'attempts')


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
        'ccm.agent': {
            'Meta': {'object_name': 'Agent'},
            'clients': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['accounts.Client']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'communications.call': {
            'Meta': {'object_name': 'Call'},
            'answered_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ccm.Agent']", 'null': 'True', 'blank': 'True'}),
            'answered_exten': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'answered_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'call_duration': ('django.db.models.fields.IntegerField', [], {}),
            'called_on': ('django.db.models.fields.DateTimeField', [], {}),
            'caller_id': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'did_number': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'ended_on': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'db_index': 'True'}),
            'unique_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'wait_duration': ('django.db.models.fields.IntegerField', [], {})
        },
        'communications.chat': {
            'Meta': {'object_name': 'Chat'},
            'ended_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {}),
            'transcript': ('django.db.models.fields.TextField', [], {})
        },
        'communications.email': {
            'Meta': {'object_name': 'Email'},
            'bccied_to': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'bounced_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'ccied_to': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '200', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delivered_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sent_from': ('django.db.models.fields.EmailField', [], {'max_length': '100', 'db_index': 'True'}),
            'sent_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sent_to': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'sent_via': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'subject': ('django.db.models.fields.TextField', [], {})
        },
        'communications.sms': {
            'Meta': {'object_name': 'SMS'},
            'attempts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'bounced_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delivered_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mask': ('django.db.models.fields.CharField', [], {'default': "'FutrBazr'", 'max_length': '15'}),
            'sent_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'sent_through': ('django.db.models.fields.CharField', [], {'default': "'netcore'", 'max_length': '20', 'blank': 'True'}),
            'sent_to': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'sms_text': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'new'", 'max_length': '15', 'db_index': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['communications']
