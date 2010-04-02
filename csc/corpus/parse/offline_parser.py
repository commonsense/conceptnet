#!/usr/bin/env python
import sys, traceback
from pcfgpattern import pattern_parse
import yaml
from csc.conceptnet.models import Sentence, Language
from django.core.paginator import Paginator
#from django.db import transaction

def process_sentence(sentence):
    print sentence.text.encode('utf-8')
    _, frametext, reltext, matches = pattern_parse(sentence.text)
    if reltext is None or reltext == 'junk': return []
    else:
        return [dict(id=sentence.id, frametext=frametext, reltext=reltext,
        matches=matches)]

def run(file, start_page=1, end_page=1000000):
    all_sentences = Sentence.objects.filter(language=Language.get('en')).order_by('id')
    paginator = Paginator(all_sentences,100)
    #pages = ((i,paginator.page(i)) for i in range(start_page,paginator.num_pages))

    def do_batch(sentences):
        preds = []
        for sentence in sentences:
            try:
                preds.extend(process_sentence(sentence))
            # changed to an improbable exception for now
            except Exception, e:
                # Add sentence
                e.sentence = sentence

                # Extract traceback
                e_type, e_value, e_tb = sys.exc_info()
                e.tb = "\n".join(traceback.format_exception( e_type, e_value, e_tb ))

                # Raise again
                raise e
        file.write('\n--- ')
        yaml.dump_all(preds, file)

    # Process sentences
    page_range = [p for p in paginator.page_range if p >= start_page and p <
    end_page]
    for i in page_range:
        sentences = paginator.page(i).object_list
        do_batch(sentences)


if __name__ == '__main__':
    start_page = int(sys.argv[1])
    end_page = int(sys.argv[2])
    out = open(sys.argv[3], 'w+')
    run(out, start_page, end_page)

