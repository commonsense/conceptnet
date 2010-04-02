
from south.db import db
from django.db import models
from csc.nl.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Deleting model 'functionclasstoword'
        db.delete_table('functionclass_words')
        
        # Changing field 'FunctionWord.functionclass'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['nl.FunctionClass']))
        db.alter_column('nl_functionword', 'functionclass_id', orm['nl.functionword:functionclass'])
        
    
    
    def backwards(self, orm):
        
        # Adding model 'functionclasstoword'
        db.create_table('functionclass_words', (
            ('functionword', orm['nl.functionclasstoword:functionword']),
            ('functionclass', orm['nl.functionclasstoword:functionclass']),
            ('id', orm['nl.functionclasstoword:id']),
        ))
        db.send_create_signal('nl', ['functionclasstoword'])
        
        # Changing field 'FunctionWord.functionclass'
        # (to signature: django.db.models.fields.related.ForeignKey(to=orm['nl.FunctionClass'], null=True))
        db.alter_column('nl_functionword', 'functionclass_id', orm['nl.functionword:functionclass'])
        
    
    
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
        'nl.functionword': {
            'functionclass': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['nl.FunctionClass']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'word': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['nl']
