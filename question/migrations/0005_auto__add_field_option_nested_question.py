# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Option.nested_question'
        db.add_column('question_option', 'nested_question', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='nested_question', to=orm['question.Question']), keep_default=True)


    def backwards(self, orm):
        
        # Deleting field 'Option.nested_question'
        db.delete_column('question_option', 'nested_question_id')


    models = {
        'question.option': {
            'Meta': {'object_name': 'Option'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nested_question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'nested_question'", 'to': "orm['question.Question']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'main_question'", 'to': "orm['question.Question']"}),
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
