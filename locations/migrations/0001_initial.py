# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Country'
        db.create_table('locations_country', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('locations', ['Country'])

        # Adding model 'State'
        db.create_table('locations_state', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Country'])),
        ))
        db.send_create_signal('locations', ['State'])

        # Adding model 'City'
        db.create_table('locations_city', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('state', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.State'])),
        ))
        db.send_create_signal('locations', ['City'])

        # Adding model 'Address'
        db.create_table('locations_address', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('line_one', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('line_two', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('line_three', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('pincode', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('city', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.City'])),
            ('state', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.State'])),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['locations.Country'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('locations', ['Address'])


    def backwards(self, orm):
        
        # Deleting model 'Country'
        db.delete_table('locations_country')

        # Deleting model 'State'
        db.delete_table('locations_state')

        # Deleting model 'City'
        db.delete_table('locations_city')

        # Deleting model 'Address'
        db.delete_table('locations_address')


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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.State']"})
        },
        'locations.country': {
            'Meta': {'object_name': 'Country'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'locations.state': {
            'Meta': {'object_name': 'State'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['locations']
