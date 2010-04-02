
from south.db import db
from django.db import models
from csc.nl.models import *

class Migration:
    
    def forwards(self, orm):
        orm.FunctionWord.objects.filter(functionclass__isnull=True).delete()
        #db.alter_column('nl_functionword', 'functionclass', models.ForeignKey(FunctionClass, null=False))
    
    def backwards(self, orm):
        raise NotImplementedError("You can't go back from here.")
    
    
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
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True'})
        },
        'nl.functionclasstoword': {
            'Meta': {'db_table': "'functionclass_words'"},
            'functionclass': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['nl.FunctionClass']"}),
            'functionword': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['nl.FunctionWord']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'nl.functionword': {
            'functionclass': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['nl.FunctionClass']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'word': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['nl']
