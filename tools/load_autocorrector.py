from csc.corpus.models import AutocorrectRule, Language
from django.db import transaction

print "Loading table..."
autocorrect_file = './autocorrect.txt'
autocorrect_kb = {}
items = filter(lambda line:line.strip()!='',open(autocorrect_file,'r').read().split('\n'))
lang_en = Language.objects.get(pk='EN')

def bulk_commit(lst):
    for obj in lst: obj.save()
bulk_commit_wrapped = transaction.commit_on_success(bulk_commit)

print "Building entries..."
ars = []
for entry in items:
    match = entry.split()[0]
    replace_with = ' '.join(entry.split()[1:])
    ar = AutocorrectRule()
    ar.language = lang_en
    ar.match = match
    ar.replace_with = replace_with
    ars.append(ar)

print "Bulk committing..."
bulk_commit_wrapped(ars)
