
from south.db import db
from django.db import models
from csc.nl.models import *

class Migration:
    
    def forwards(self, orm):
        for obj in orm.FunctionClassToWord.objects.all():
            lang = obj.functionword.language
            word = obj.functionword.word
            klass = obj.functionclass
            print lang, word, klass
            if FunctionWord.objects.filter(language=lang, word=word,
            functionclass=klass).count() == 0:
                FunctionWord.objects.create(language=lang, word=word,
                functionclass=klass)
    
    
    def backwards(self, orm):
        FunctionWord.objects.filter(functionclass__isnull=False).delete()
    
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
