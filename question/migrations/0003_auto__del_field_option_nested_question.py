# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting field 'Option.nested_question'
        db.delete_column('question_option', 'nested_question_id')

        # Adding M2M table for field nested_question on 'Option'
        db.create_table('question_option_nested_question', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('option', models.ForeignKey(orm['question.option'], null=False)),
            ('question', models.ForeignKey(orm['question.question'], null=False))
        ))
        db.create_unique('question_option_nested_question', ['option_id', 'question_id'])


    def backwards(self, orm):
        
        # Adding field 'Option.nested_question'
        db.add_column('question_option', 'nested_question', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='Nested Question', to=orm['question.Question']), keep_default=False)

        # Removing M2M table for field nested_question on 'Option'
        db.delete_table('question_option_nested_question')


    models = {
        'question.option': {
            'Meta': {'object_name': 'Option'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nested_question': ('django.db.models.fields.related.ManyToManyField', [], {'default': 'None', 'related_name': "'Nested Question'", 'symmetrical': 'False', 'to': "orm['question.Question']"}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['question.Question']"}),
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
