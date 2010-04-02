
from south.db import db
from south.models import MigrationHistory
from django.db import models
from csc.conceptnet.models import *

class Migration:
    
    def forwards(self, orm):
        if MigrationHistory.objects.filter(app_name='conceptnet4', migration='0001_initial').count() > 0:
            print "Skipping initial migration: it was applied under the name 'conceptnet4'."
            return        
        
        # Adding model 'Assertion'
        db.create_table('assertions', (
            ('id', orm['conceptnet.Assertion:id']),
            ('language', orm['conceptnet.Assertion:language']),
            ('relation', orm['conceptnet.Assertion:relation']),
            ('concept1', orm['conceptnet.Assertion:concept1']),
            ('concept2', orm['conceptnet.Assertion:concept2']),
            ('score', orm['conceptnet.Assertion:score']),
            ('frequency', orm['conceptnet.Assertion:frequency']),
            ('best_surface1', orm['conceptnet.Assertion:best_surface1']),
            ('best_surface2', orm['conceptnet.Assertion:best_surface2']),
            ('best_raw_id', orm['conceptnet.Assertion:best_raw_id']),
            ('best_frame', orm['conceptnet.Assertion:best_frame']),
        ))
        db.send_create_signal('conceptnet', ['Assertion'])
        
        # Adding model 'UserData'
        db.create_table('conceptnet_userdata', (
            ('id', orm['conceptnet.UserData:id']),
            ('created', orm['conceptnet.UserData:created']),
            ('updated', orm['conceptnet.UserData:updated']),
            ('user', orm['conceptnet.UserData:user']),
            ('activity', orm['conceptnet.UserData:activity']),
        ))
        db.send_create_signal('conceptnet', ['UserData'])
        
        # Adding model 'RawAssertion'
        db.create_table('raw_assertions', (
            ('id', orm['conceptnet.RawAssertion:id']),
            ('created', orm['conceptnet.RawAssertion:created']),
            ('updated', orm['conceptnet.RawAssertion:updated']),
            ('sentence', orm['conceptnet.RawAssertion:sentence']),
            ('assertion', orm['conceptnet.RawAssertion:assertion']),
            ('creator', orm['conceptnet.RawAssertion:creator']),
            ('surface1', orm['conceptnet.RawAssertion:surface1']),
            ('surface2', orm['conceptnet.RawAssertion:surface2']),
            ('frame', orm['conceptnet.RawAssertion:frame']),
            ('batch', orm['conceptnet.RawAssertion:batch']),
            ('language', orm['conceptnet.RawAssertion:language']),
            ('score', orm['conceptnet.RawAssertion:score']),
        ))
        db.send_create_signal('conceptnet', ['RawAssertion'])
        
        # Adding model 'Concept'
        db.create_table('concepts', (
            ('id', orm['conceptnet.Concept:id']),
            ('language', orm['conceptnet.Concept:language']),
            ('text', orm['conceptnet.Concept:text']),
            ('num_assertions', orm['conceptnet.Concept:num_assertions']),
            ('words', orm['conceptnet.Concept:words']),
            ('visible', orm['conceptnet.Concept:visible']),
        ))
        db.send_create_signal('conceptnet', ['Concept'])
        
        # Adding model 'Frame'
        db.create_table('conceptnet_frames', (
            ('id', orm['conceptnet.Frame:id']),
            ('language', orm['conceptnet.Frame:language']),
            ('text', orm['conceptnet.Frame:text']),
            ('relation', orm['conceptnet.Frame:relation']),
            ('goodness', orm['conceptnet.Frame:goodness']),
            ('frequency', orm['conceptnet.Frame:frequency']),
            ('question_yn', orm['conceptnet.Frame:question_yn']),
            ('question1', orm['conceptnet.Frame:question1']),
            ('question2', orm['conceptnet.Frame:question2']),
        ))
        db.send_create_signal('conceptnet', ['Frame'])
        
        # Adding model 'Batch'
        db.create_table('parsing_batch', (
            ('id', orm['conceptnet.Batch:id']),
            ('created', orm['conceptnet.Batch:created']),
            ('updated', orm['conceptnet.Batch:updated']),
            ('owner', orm['conceptnet.Batch:owner']),
            ('status', orm['conceptnet.Batch:status']),
            ('remarks', orm['conceptnet.Batch:remarks']),
            ('progress_num', orm['conceptnet.Batch:progress_num']),
            ('progress_den', orm['conceptnet.Batch:progress_den']),
        ))
        db.send_create_signal('conceptnet', ['Batch'])
        
        # Adding model 'SurfaceForm'
        db.create_table('surface_forms', (
            ('id', orm['conceptnet.SurfaceForm:id']),
            ('language', orm['conceptnet.SurfaceForm:language']),
            ('concept', orm['conceptnet.SurfaceForm:concept']),
            ('text', orm['conceptnet.SurfaceForm:text']),
            ('residue', orm['conceptnet.SurfaceForm:residue']),
            ('use_count', orm['conceptnet.SurfaceForm:use_count']),
        ))
        db.send_create_signal('conceptnet', ['SurfaceForm'])
        
        # Adding model 'Relation'
        db.create_table('predicatetypes', (
            ('id', orm['conceptnet.Relation:id']),
            ('name', orm['conceptnet.Relation:name']),
            ('description', orm['conceptnet.Relation:description']),
        ))
        db.send_create_signal('conceptnet', ['Relation'])
        
        # Creating unique_together for [language, text] on SurfaceForm.
        db.create_unique('surface_forms', ['language_id', 'text'])
        
        # Creating unique_together for [relation, concept1, concept2, frequency, language] on Assertion.
        db.create_unique('assertions', ['relation_id', 'concept1_id', 'concept2_id', 'frequency_id', 'language_id'])
        
        # Creating unique_together for [language, text] on Concept.
        db.create_unique('concepts', ['language_id', 'text'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [language, text] on Concept.
        db.delete_unique('concepts', ['language_id', 'text'])
        
        # Deleting unique_together for [relation, concept1, concept2, frequency, language] on Assertion.
        db.delete_unique('assertions', ['relation_id', 'concept1_id', 'concept2_id', 'frequency_id', 'language_id'])
        
        # Deleting unique_together for [language, text] on SurfaceForm.
        db.delete_unique('surface_forms', ['language_id', 'text'])
        
        # Deleting model 'Assertion'
        db.delete_table('assertions')
        
        # Deleting model 'UserData'
        db.delete_table('conceptnet_userdata')
        
        # Deleting model 'RawAssertion'
        db.delete_table('raw_assertions')
        
        # Deleting model 'Concept'
        db.delete_table('concepts')
        
        # Deleting model 'Frame'
        db.delete_table('conceptnet_frames')
        
        # Deleting model 'Batch'
        db.delete_table('parsing_batch')
        
        # Deleting model 'SurfaceForm'
        db.delete_table('surface_forms')
        
        # Deleting model 'Relation'
        db.delete_table('predicatetypes')
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
        },
        'conceptnet.assertion': {
            'Meta': {'unique_together': "(('relation', 'concept1', 'concept2', 'frequency', 'language'),)", 'db_table': "'assertions'"},
            'best_frame': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['conceptnet.Frame']", 'null': 'True'}),
            'best_raw_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'best_surface1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'left_assertion_set'", 'null': 'True', 'to': "orm['conceptnet.SurfaceForm']"}),
            'best_surface2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'right_assertion_set'", 'null': 'True', 'to': "orm['conceptnet.SurfaceForm']"}),
            'concept1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'left_assertion_set'", 'to': "orm['conceptnet.Concept']"}),
            'concept2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'right_assertion_set'", 'to': "orm['conceptnet.Concept']"}),
            'frequency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['nl.Frequency']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'relation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['conceptnet.Relation']"}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'votes': ('django.contrib.contenttypes.generic.GenericRelation', [], {'to': "orm['voting.Vote']"})
        },
        'conceptnet.batch': {
            'Meta': {'db_table': "'parsing_batch'"},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'progress_den': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'progress_num': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'remarks': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {})
        },
        'conceptnet.concept': {
            'Meta': {'unique_together': "(('language', 'text'),)", 'db_table': "'concepts'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'num_assertions': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'text': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'words': ('django.db.models.fields.IntegerField', [], {})
        },
        'conceptnet.frame': {
            'Meta': {'db_table': "'conceptnet_frames'"},
            'frequency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['nl.Frequency']"}),
            'goodness': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'question1': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'question2': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'question_yn': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'relation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['conceptnet.Relation']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'conceptnet.rawassertion': {
            'Meta': {'db_table': "'raw_assertions'"},
            'assertion': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['conceptnet.Assertion']", 'null': 'True'}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['conceptnet.Batch']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'frame': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['conceptnet.Frame']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sentence': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Sentence']", 'null': 'True'}),
            'surface1': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'left_rawassertion_set'", 'to': "orm['conceptnet.SurfaceForm']"}),
            'surface2': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'right_rawassertion_set'", 'to': "orm['conceptnet.SurfaceForm']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {}),
            'votes': ('django.contrib.contenttypes.generic.GenericRelation', [], {'to': "orm['voting.Vote']"})
        },
        'conceptnet.relation': {
            'Meta': {'db_table': "'predicatetypes'"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'unique': 'True'})
        },
        'conceptnet.surfaceform': {
            'Meta': {'unique_together': "(('language', 'text'),)", 'db_table': "'surface_forms'"},
            'concept': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['conceptnet.Concept']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'residue': ('django.db.models.fields.TextField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'use_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'conceptnet.userdata': {
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Activity']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'corpus.language': {
            'id': ('django.db.models.fields.CharField', [], {'max_length': '16', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sentence_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'corpus.sentence': {
            'Meta': {'db_table': "'sentences'"},
            'activity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Activity']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'votes': ('django.contrib.contenttypes.generic.GenericRelation', [], {'to': "orm['voting.Vote']"})
        },
        'events.activity': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
        },
        'nl.frequency': {
            'Meta': {'unique_together': "(('language', 'text'),)", 'db_table': "'conceptnet_frequency'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        'voting.vote': {
            'Meta': {'unique_together': "(('user', 'content_type', 'object_id'),)", 'db_table': "'votes'"},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'vote': ('django.db.models.fields.SmallIntegerField', [], {})
        }
    }
    
    complete_apps = ['conceptnet']
