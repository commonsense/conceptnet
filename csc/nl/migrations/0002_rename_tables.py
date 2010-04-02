
from south.db import db
from django.db import models
from csc.nl.models import *

class Migration:
    
    def forwards(self, orm):
        db.rename_table('conceptnet_frequency', 'nl_frequency')
        db.rename_table('corpus_autoreplacerule', 'nl_autoreplacerule')
        db.rename_table('functionwords', 'nl_functionword')
        db.rename_table('functionclass', 'nl_functionclass')
    
    def backwards(self, orm):
        db.rename_table('nl_frequency', 'conceptnet_frequency')
        db.rename_table('nl_autoreplacerule', 'corpus_autoreplacerule')
        db.rename_table('nl_functionword', 'functionwords')
        db.rename_table('nl_functionclass', 'functionclass')
    
    models = {
        'corpus.language': {
            'id': ('django.db.models.fields.CharField', [], {'max_length': '16', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sentence_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'nl.autoreplacerule': {
            'family': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'match': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'replace_with': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'nl.frequency': {
            'Meta': {'unique_together': "(('language', 'text'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        'nl.functionclass': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'words': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['nl.FunctionWord']"})
        },
        'nl.functionword': {
            'Meta': {'db_table': "'nl_functionwords'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'word': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['nl']
