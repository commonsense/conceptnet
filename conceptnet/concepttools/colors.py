from csc.divisi.util import get_picklecached_thing
from csc.divisi.blend import Blend
from csc.divisi.flavors import ConceptByFeatureMatrix
from csc.conceptnet.models import en
from csc.conceptnet.analogyspace import conceptnet_2d_from_db, make_category
import os

try:
    FILEPATH = os.path.dirname(__file__) or '.'
except NameError:
    FILEPATH = '.'

def _make_color_matrix():
    matrixlist = []
    for file in os.listdir('./context'):
        color = file.split('.')[0]
        fstream = open('./context/' + file,'r')
        sets = [x.strip('\n') for x in fstream.readlines()]
        clist = ','.join(sets)
        words = clist.split(',')
        for word in words:
            word = word.strip()
            if word == '': continue
            print color, word
            matrixlist.append(((word, 'HasColor', color), 10))
            matrixlist.append(((word, 'HasProperty', 'colorful'), 10))
            matrixlist.append(((word, 'HasProperty', color), 10))
        matrixlist.append(((color, 'HasColor', color), 50))
        matrixlist.append(((color, 'HasProperty', color), 50))
    return ConceptByFeatureMatrix.from_triples(matrixlist)
              
def _get_color_blend():
    colors = get_picklecached_thing(FILEPATH+os.sep+'colormatrix.pickle.gz', _make_color_matrix)
    cnet = get_picklecached_thing(FILEPATH+os.sep+'cnet.pickle.gz', lambda: conceptnet_2d_from_db('en'))
    colorblend = Blend([colors, cnet]).normalized(mode=[0,1]).bake()
    return colorblend

colorblend = get_picklecached_thing(FILEPATH+os.sep+'colorblend.pickle.gz', _get_color_blend)
thesvd = colorblend.svd(k=100)
colorful_concepts = thesvd.u.label_list(0)
#print thesvd.summarize(10)
colorful_vec = thesvd.v[('right', u'HasProperty', u'colorful'), :]
colorlist = ['blue', 'black', 'brown', 'green', 'grey', 'orange', 'pink', 'purple', 'red', 'white', 'yellow']
rgb = {'blue': (0,0,255), 'black': (0,0,0), 'brown': (139, 69, 19), 'green': (0, 255, 0), 'grey': (100,100,100), 'orange': (255, 165,0), 'pink': (255,105,180), 'purple': (160, 32, 240), 'red': (255,0,0), 'white': (255, 255, 255), 'yellow': (255,255,0)}
#colorvecs = [(x, thesvd.weighted_u[x,:]) for x in colorlist]
colorvecs = [(x, thesvd.weighted_u[x,:]*.1 + thesvd.weighted_v[('right', 'HasColor', x),:]) for x in colorlist]

def how_colorful(word, thesvd):
    wordvc = thesvd.weighted_u[word,:]
    return wordvc.hat() * make_category(thesvd, concepts=rgb.keys())

def _get_color_mix(adhoc, thesvd):
    vec_dict = {}
    totalsim = 0.0
    for cur_color, vec in colorvecs:
        sim = adhoc.hat() * vec.hat()
        vec_dict[cur_color] = sim**3
        totalsim += sim**3
    if totalsim == 0.0: return vec_dict
    for color in vec_dict:
        vec_dict[color] /= totalsim
    return vec_dict

def _make_color(words, thesvd):
    feats = [('left', 'HasColor', word) for word in words]
    try:
#        words = [x for x in words if abs(how_colorful(x, thesvd)) > 0.001]
        adhoc = make_category(thesvd, concepts=words)
    except KeyError:
        return (128, 128, 128)
    mix = _get_color_mix(adhoc, thesvd)
    new_color = (0,0,0)
    for color, weight in mix.items():
        cur_color = tuple(item*weight for item in rgb[color])
        new_color = tuple(a+b for a,b in zip(cur_color, new_color))
        new_color = tuple(min(max(int(c), 0), 255) for c in new_color)
    return new_color

def _process_phrase(text, thesvd):
    parts = en.nl.extract_concepts(text, 3, True) 
    return _make_color(parts, thesvd)

def concept_color(concept):
    if hasattr(concept, 'text'): concept = concept.text
    else: concept = en.nl.normalize(concept)
    return _make_color([concept], thesvd)

def text_color(text):
    return _process_phrase(text, thesvd)

def colorize(sent):
    parts = en.nl.extract_concepts(sent, 2, True)
    parts = [x for x in parts if x in colorful_concepts]
    full_color = _make_color(parts, thesvd)
    outdict = {'sent*': full_color}
    for word in parts:
        wordcolor = _make_color([word], thesvd)
        colorstrength = how_colorful(word,thesvd)
        outdict[word] = (wordcolor, colorstrength)
    return outdict

def color_sent_and_some_parts(sentence):
    # Catherine's version, w/o bigrams
    parts = colorize(sentence)
    sent_color = parts['sent*']
    overall_color = text_color(sentence)
    htmltext = u'<div style="background-color: rgb(%d,%d,%d); padding: 1ex;">' % overall_color
    words = en.nl.tokenize(sentence).split()
    wordpos = 0
    while wordpos < len(words):
        word = words[wordpos]
        if word in parts.keys():
            if word == 'sent*': continue
            wordcolor = parts[word][0]
            strength = parts[word][1]
            if abs(strength) < 1:
                htmltext += word+' '
            else:
                print wordcolor
                htmltext += '<span style="background-color: rgb(%d,%d,%d)">' % wordcolor
                htmltext += word
                htmltext += '</span> '
        else:
            htmltext += word+' '
        wordpos += 1
    htmltext += '</div>'
    return htmltext
    
def html_color_sentence(sentence):
    # warning: this code sucks
    overall_color = text_color(sentence)
    htmltext = u'<div style="background-color: rgb(%d,%d,%d); padding: 1ex;">' % overall_color
    words = en.nl.tokenize(sentence).split()
    wordpos = 0
    while wordpos < len(words):
        word = words[wordpos]
        color = None
        if not en.nl.is_stopword(word):
            text = None
            for words_ahead in (3, 2, 1):
                if wordpos+words_ahead > len(words): continue
                if en.nl.is_stopword(words[wordpos+words_ahead-1]): continue
                text = ' '.join(words[wordpos:wordpos+words_ahead])
                if en.nl.normalize(text) in colorful_concepts:
                    color = concept_color(text)
                    break
            if color is None:
                htmltext += word+' '
            else:
                htmltext += '<span style="background-color: rgb(%d,%d,%d)">' % color
                htmltext += text
                htmltext += '</span> '
            wordpos += words_ahead
        else:
            htmltext += word+' '
            wordpos += 1
    htmltext += '</div>'
    return htmltext

def html_color_text(text):
    # TODO: better tokenizer
    sentences = text.split('\n')
    return u'\n'.join(color_sent_and_some_parts(s) for s in sentences)

import codecs

def html_color_file(filename):
    text = codecs.open(filename, encoding='utf-8').read()
    out = codecs.open(filename+'.html', 'w', encoding='utf-8')
    out.write('<!doctype html>\n')
    main_color = text_color(text)
    out.write('<html><body style="background-color: rgb(%d,%d,%d); color: #444;">\n' % main_color)
    out.write(html_color_text(text))
    out.write('</body></html>\n')
    out.close()

def demo():
    import sys
    try:
        filename = sys.argv[1]
    except IndexError:
        raise ValueError("To run this as a script, please give the filename of a text file.")
    html_color_file(filename)

if __name__ == '__main__': demo()
