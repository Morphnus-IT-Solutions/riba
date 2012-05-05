# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Option'
        #db.delete_table('question_option')

        # Adding field 'Question.parent'
        db.add_column('question_question', 'parent', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='parent_question', blank=True, to=orm['question.Question']), keep_default=True)

        # Adding field 'Question.parent_value'
        db.add_column('question_question', 'parent_value', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True), keep_default=True)


    def backwards(self, orm):
        
        # Adding model 'Option'
        db.create_table('question_option', (
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='main_question', to=orm['question.Question'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('nested_question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='nested_question', to=orm['question.Question'])),
        ))
        db.send_create_signal('question', ['Option'])

        # Deleting field 'Question.parent'
        db.delete_column('question_question', 'parent_id')

        # Deleting field 'Question.parent_value'
        db.delete_column('question_question', 'parent_value')


    models = {
        'question.question': {
            'Meta': {'object_name': 'Question'},
            'answer_type': ('django.db.models.fields.CharField', [], {'default': "'char'", 'max_length': '15', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_dynamic': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': "''", 'related_name': "'parent_question'", 'blank': 'True', 'to': "orm['question.Question']"}),
            'parent_value': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'normal'", 'max_length': '10', 'db_index': 'True'})
        }
    }

    complete_apps = ['question']
