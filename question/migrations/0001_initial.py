# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Question'
        db.create_table('question_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default='normal', max_length=10, db_index=True)),
            ('question', self.gf('django.db.models.fields.TextField')()),
            ('answer_type', self.gf('django.db.models.fields.CharField')(default='char', max_length=15, db_index=True)),
            ('is_dynamic', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('question', ['Question'])

        # Adding model 'Option'
        db.create_table('question_option', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('nested_question', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['question.Question'])),
        ))
        db.send_create_signal('question', ['Option'])


    def backwards(self, orm):
        
        # Deleting model 'Question'
        db.delete_table('question_question')

        # Deleting model 'Option'
        db.delete_table('question_option')


    models = {
        'question.option': {
            'Meta': {'object_name': 'Option'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nested_question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['question.Question']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'question.question': {
            'Meta': {'object_name': 'Question'},
            'answer_type': ('django.db.models.fields.CharField', [], {'default': "'char'", 'max_length': '15', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_dynamic': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'normal'", 'max_length': '10', 'db_index': 'True'})
        }
    }

    complete_apps = ['question']
