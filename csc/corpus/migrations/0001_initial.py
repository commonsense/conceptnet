
from south.db import db
from django.db import models
from csc.corpus.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'TaggedSentence'
        db.create_table('tagged_sentences', (
            ('text', orm['corpus.TaggedSentence:text']),
            ('language', orm['corpus.TaggedSentence:language']),
            ('sentence', orm['corpus.TaggedSentence:sentence']),
        ))
        db.send_create_signal('corpus', ['TaggedSentence'])
        
        # Adding model 'Language'
        db.create_table('corpus_language', (
            ('id', orm['corpus.Language:id']),
            ('name', orm['corpus.Language:name']),
            ('sentence_count', orm['corpus.Language:sentence_count']),
        ))
        db.send_create_signal('corpus', ['Language'])
        
        # Adding model 'DependencyParse'
        db.create_table('dependency_parses', (
            ('id', orm['corpus.DependencyParse:id']),
            ('sentence', orm['corpus.DependencyParse:sentence']),
            ('linktype', orm['corpus.DependencyParse:linktype']),
            ('word1', orm['corpus.DependencyParse:word1']),
            ('word2', orm['corpus.DependencyParse:word2']),
            ('index1', orm['corpus.DependencyParse:index1']),
            ('index2', orm['corpus.DependencyParse:index2']),
        ))
        db.send_create_signal('corpus', ['DependencyParse'])
        
        # Adding model 'Sentence'
        db.create_table('sentences', (
            ('id', orm['corpus.Sentence:id']),
            ('text', orm['corpus.Sentence:text']),
            ('creator', orm['corpus.Sentence:creator']),
            ('created_on', orm['corpus.Sentence:created_on']),
            ('language', orm['corpus.Sentence:language']),
            ('activity', orm['corpus.Sentence:activity']),
            ('score', orm['corpus.Sentence:score']),
        ))
        db.send_create_signal('corpus', ['Sentence'])
        
    
    
    def backwards(self, orm):
        
        # Deleting model 'TaggedSentence'
        db.delete_table('tagged_sentences')
        
        # Deleting model 'Language'
        db.delete_table('corpus_language')
        
        # Deleting model 'DependencyParse'
        db.delete_table('dependency_parses')
        
        # Deleting model 'Sentence'
        db.delete_table('sentences')
        
    
    
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
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'corpus.dependencyparse': {
            'Meta': {'db_table': "'dependency_parses'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index1': ('django.db.models.fields.IntegerField', [], {}),
            'index2': ('django.db.models.fields.IntegerField', [], {}),
            'linktype': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'sentence': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Sentence']"}),
            'word1': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'word2': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        'corpus.taggedsentence': {
            'Meta': {'db_table': "'tagged_sentences'"},
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'sentence': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Sentence']", 'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'events.activity': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {})
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
    
    complete_apps = ['corpus']
