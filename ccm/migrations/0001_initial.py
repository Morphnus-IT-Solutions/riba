# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Agent'
        db.create_table('ccm_agent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=30, db_index=True)),
        ))
        db.send_create_signal('ccm', ['Agent'])

        # Adding M2M table for field clients on 'Agent'
        db.create_table('ccm_agent_clients', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('agent', models.ForeignKey(orm['ccm.agent'], null=False)),
            ('client', models.ForeignKey(orm['accounts.client'], null=False))
        ))
        db.create_unique('ccm_agent_clients', ['agent_id', 'client_id'])

        # Adding model 'Extension'
        db.create_table('ccm_extension', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('protocol', self.gf('django.db.models.fields.CharField')(default='sip', max_length=15, db_index=True)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=10, db_index=True)),
            ('pin', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('allotted_to', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ccm.Agent'])),
        ))
        db.send_create_signal('ccm', ['Extension'])

        # Adding unique constraint on 'Extension', fields ['protocol', 'number']
        db.create_unique('ccm_extension', ['protocol', 'number'])

        # Adding model 'Queue'
        db.create_table('ccm_queue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('ccm', ['Queue'])


    def backwards(self, orm):
        
        # Deleting model 'Agent'
        db.delete_table('ccm_agent')

        # Removing M2M table for field clients on 'Agent'
        db.delete_table('ccm_agent_clients')

        # Deleting model 'Extension'
        db.delete_table('ccm_extension')

        # Removing unique constraint on 'Extension', fields ['protocol', 'number']
        db.delete_unique('ccm_extension', ['protocol', 'number'])

        # Deleting model 'Queue'
        db.delete_table('ccm_queue')


    models = {
        'accounts.client': {
            'Meta': {'object_name': 'Client'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        'ccm.agent': {
            'Meta': {'object_name': 'Agent'},
            'clients': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['accounts.Client']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'ccm.extension': {
            'Meta': {'unique_together': "(('protocol', 'number'),)", 'object_name': 'Extension'},
            'allotted_to': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ccm.Agent']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'db_index': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'protocol': ('django.db.models.fields.CharField', [], {'default': "'sip'", 'max_length': '15', 'db_index': 'True'})
        },
        'ccm.queue': {
            'Meta': {'object_name': 'Queue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['ccm']
