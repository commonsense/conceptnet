
from south.db import db
from django.db import models
from csc.nl.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Adding model 'Frequency'
        db.create_table('conceptnet_frequency', (
            ('id', orm['nl.Frequency:id']),
            ('language', orm['nl.Frequency:language']),
            ('text', orm['nl.Frequency:text']),
            ('value', orm['nl.Frequency:value']),
        ))
        db.send_create_signal('nl', ['Frequency'])
        
        # Adding model 'AutoreplaceRule'
        db.create_table('corpus_autoreplacerule', (
            ('id', orm['nl.AutoreplaceRule:id']),
            ('language', orm['nl.AutoreplaceRule:language']),
            ('family', orm['nl.AutoreplaceRule:family']),
            ('match', orm['nl.AutoreplaceRule:match']),
            ('replace_with', orm['nl.AutoreplaceRule:replace_with']),
        ))
        db.send_create_signal('nl', ['AutoreplaceRule'])
        
        # Adding model 'FunctionClass'
        db.create_table('functionclass', (
            ('id', orm['nl.FunctionClass:id']),
            ('name', orm['nl.FunctionClass:name']),
        ))
        db.send_create_signal('nl', ['FunctionClass'])
        
        # Adding model 'FunctionWord'
        db.create_table('functionwords', (
            ('id', orm['nl.FunctionWord:id']),
            ('language', orm['nl.FunctionWord:language']),
            ('word', orm['nl.FunctionWord:word']),
        ))
        db.send_create_signal('nl', ['FunctionWord'])
        
        # Adding ManyToManyField 'FunctionClass.words'
        db.create_table('functionclass_words', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('functionclass', models.ForeignKey(orm.FunctionClass, null=False)),
            ('functionword', models.ForeignKey(orm.FunctionWord, null=False))
        ))
        
        # Creating unique_together for [language, text] on Frequency.
        db.create_unique('conceptnet_frequency', ['language_id', 'text'])
        
    
    
    def backwards(self, orm):
        
        # Deleting unique_together for [language, text] on Frequency.
        db.delete_unique('conceptnet_frequency', ['language_id', 'text'])
        
        # Deleting model 'Frequency'
        db.delete_table('conceptnet_frequency')
        
        # Deleting model 'AutoreplaceRule'
        db.delete_table('corpus_autoreplacerule')
        
        # Deleting model 'FunctionClass'
        db.delete_table('functionclass')
        
        # Deleting model 'FunctionWord'
        db.delete_table('functionwords')
        
        # Dropping ManyToManyField 'FunctionClass.words'
        db.delete_table('functionclass_words')
        
    
    
    models = {
        'corpus.language': {
            'id': ('django.db.models.fields.CharField', [], {'max_length': '16', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sentence_count': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'nl.autoreplacerule': {
            'Meta': {'db_table': "'corpus_autoreplacerule'"},
            'family': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'match': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'replace_with': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'nl.frequency': {
            'Meta': {'unique_together': "(('language', 'text'),)", 'db_table': "'conceptnet_frequency'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        'nl.functionclass': {
            'Meta': {'db_table': "'functionclass'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'words': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['nl.FunctionWord']"})
        },
        'nl.functionword': {
            'Meta': {'db_table': "'functionwords'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['corpus.Language']"}),
            'word': ('django.db.models.fields.TextField', [], {})
        }
    }
    
    complete_apps = ['nl']
