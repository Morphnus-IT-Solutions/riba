# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'City.type'
        db.add_column('locations_city', 'type', self.gf('django.db.models.fields.CharField')(default='primary', max_length='15', db_index=True), keep_default=False)

        # Adding field 'City.normalized'
        db.add_column('locations_city', 'normalized', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.City'], null=True, blank=True), keep_default=False)

        # Adding index on 'City', fields ['name']
        db.create_index('locations_city', ['name'])

        # Adding field 'State.type'
        db.add_column('locations_state', 'type', self.gf('django.db.models.fields.CharField')(default='primary', max_length='15', db_index=True), keep_default=False)

        # Adding field 'State.normalized'
        db.add_column('locations_state', 'normalized', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.State'], null=True, blank=True), keep_default=False)

        # Adding index on 'State', fields ['name']
        db.create_index('locations_state', ['name'])

        # Adding field 'Country.type'
        db.add_column('locations_country', 'type', self.gf('django.db.models.fields.CharField')(default='primary', max_length='15', db_index=True), keep_default=False)

        # Adding field 'Country.normalized'
        db.add_column('locations_country', 'normalized', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Country'], null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'City.type'
        db.delete_column('locations_city', 'type')

        # Deleting field 'City.normalized'
        db.delete_column('locations_city', 'normalized_id')

        # Removing index on 'City', fields ['name']
        db.delete_index('locations_city', ['name'])

        # Deleting field 'State.type'
        db.delete_column('locations_state', 'type')

        # Deleting field 'State.normalized'
        db.delete_column('locations_state', 'normalized_id')

        # Removing index on 'State', fields ['name']
        db.delete_index('locations_state', ['name'])

        # Deleting field 'Country.type'
        db.delete_column('locations_country', 'type')

        # Deleting field 'Country.normalized'
        db.delete_column('locations_country', 'normalized_id')


    models = {
        'locations.address': {
            'Meta': {'object_name': 'Address'},
            'city': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']"}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_one': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'line_three': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'line_two': ('django.db.models.fields.CharField', [], {'max_length': '500', 'blank': 'True'}),
            'pincode': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'locations.city': {
            'Meta': {'object_name': 'City'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.City']", 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': "'15'", 'db_index': 'True'})
        },
        'locations.country': {
            'Meta': {'object_name': 'Country'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': "'15'", 'db_index': 'True'})
        },
        'locations.state': {
            'Meta': {'object_name': 'State'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'db_index': 'True'}),
            'normalized': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'primary'", 'max_length': "'15'", 'db_index': 'True'})
        }
    }

    complete_apps = ['locations']
