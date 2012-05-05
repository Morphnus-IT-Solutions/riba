# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'DuplicateUsers'
        db.create_table('migration_duplicateusers', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('duplicate', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('original', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('migration', ['DuplicateUsers'])

        # Adding model 'AccountUserMap'
        db.create_table('migration_accountusermap', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('account', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.Account'])),
            ('user_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('migration', ['AccountUserMap'])


    def backwards(self, orm):
        
        # Deleting model 'DuplicateUsers'
        db.delete_table('migration_duplicateusers')

        # Deleting model 'AccountUserMap'
        db.delete_table('migration_accountusermap')


    models = {
        'accounts.account': {
            'Meta': {'object_name': 'Account'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'customer_support_no': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
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
        'migration.accountusermap': {
            'Meta': {'object_name': 'AccountUserMap'},
            'account': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['accounts.Account']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'migration.duplicateusers': {
            'Meta': {'object_name': 'DuplicateUsers'},
            'duplicate': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'original': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['migration']
