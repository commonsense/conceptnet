#python-encoding: UTF-8

from csc.conceptnet4.models import Concept
from csc.nl.ja.system import *
from csc.corpus.models import *
import MeCab

def GetConcept(concept, lang):
    strings = []

    if not Concept.exists(concept, lang):
        print '{'
        print '\tword = "%s",' % concept
        print '\terror = "Word not found!",'
        print '}'
        return None

    result = Concept.get(concept, lang)

    lang       = result.language.name
    word       = result.text
    assertions = str(result.num_assertions)

    relations = {}

    for item in result.get_assertions():
        if not (item.relation.name in relations):
            relations[item.relation.name] = []

        relations[item.relation.name].append(
        {
            '-- comment': item.__str__(),
            'first':      item.concept1.text,
            'second':     item.concept2.text,
            'score':      item.score,
            'frequency':  item.frequency.value,
            'mods':       '',
        })

    print '{'
    print '\tword = "%s",'     % word
    print '\tlang = "%s",'     % lang
    print '\tassertions = %s,' % assertions

    for item.relation.name in relations:
        print '\t', item.relation.name, ' ='
        print '\t{'

        for v in relations[item.relation.name]:
            print '\t\t{'
            if v['first'] != word:
                print '\t\t\tfirst = "%s",' % v['first']
            else:
                print '\t\t\tsecond = "%s",' % v['second']

            if v['mods'] != '':
                print '\t\t\tmods = "%s",' % v['mods']

            print '\t\t\tscore = %d,' % v['score']
            print '\t\t\tfrequency = %d,' % v['frequency']

            print '\t\t},'

        print '\t},'

    print '}'

    return result

####################################################################################################
## Main ############################################################################################
####################################################################################################

j        = Language.get('ja')
j_s      = Sentence.objects.filter(language=j)
e        = Language.get('en')
e_s      = Sentence.objects.filter(language=e)
parser   = JaParser()

u = \
[
    parser.parse_string(v) for v in \
    [
        '赤いappleが9月に生える。',
        'が',
        'は',
        'を',
        '1月',
        '１月',
        '私の彼って、最近車買ったんだよぉ？明日は軽井沢へ連れて行ってくれるんだぁ',
        '外国人はよく社会問題の原因だとせめられ、差別されるものです。',
        'すてきな人に会いたい。',
        '大きな人に会いたい。',
        '大きい人に会いたい。',
        '赤い花は素敵。',
        'アメリカには白人がいっぱい住んでいます。',
        'テストには問題ない。',
        '夏休みに見に行った畑のいちごがとても赤かった。',
        '今すぐ行かなければならない。',
        '今日は寝てしまいました。',
        '君に今すぐ会いたい',
        'この毛布は暖かくなかった。',
        'この毛布は暖かくなるんだろう。',
        '彼女のかみが細かくて更々です。',
        '素敵な人に会いたい。',
        '教授が「分かった」とさけた。',
        '教授が「分かった」とさけた。',
        '事実はそうではなかった。',
        '米がやすくならなければならなくはないだろう。',
        'その帽子が綺麗です。',
        'その帽子が綺麗でした。',
        'その帽子が綺麗だ。',
        'その帽子が綺麗だった。',
        'その帽子が綺麗である。',
        'その帽子が綺麗であった。',
        '春は寒いであって寂しい時期である。',
        'この世の中じゃ、人間には説明できないことだってあるよ！',
        '赤い',
        '赤くない',
        '赤かった',
        '赤くなかった',
        '赤いです',
        '赤いではありません',
        '赤いじゃありません',
        '赤いではありませんでした',
        '顔が赤くなった',
        '顔が赤くなってしまいました',
        '顔が赤くならなかった',
        '君が面白くなりました',
        '君が結局面白くならなかった',
        'アメリカへのお客様にお知らせします。',
        '札幌には牛乳が人気である。',
        'コンピュータの世界では「モニタ」とは出力の仕方の一種だ。',
        '説明することが無理なときがある。',
        '8月にリンゴが赤くなる',
        '8月にリンゴを赤くする',
        '8月にリンゴを赤くしてやる',
        '8月にリンゴを赤くしておく',
        '人間は哺乳類の一種である',
        'あなたが会議の際にすることの一つは資料を配布するである．',
        'とうもろこしは地面でなくても育つことができる．',
        '',
    ]
]

def listUtterances(start = 0, count = -1):
    if count < 0: count = len(u)

    for i in range(start, count):
        print('[' + str(i) + '] : ' + u[i].surface)

def dumpUtterances(start = -1, count = -1):
    if start < 0 and count < 0:
        start = 0
        count = len(u)

    elif count == -1:
        count = 1

    count = min(len(u) - start, count)

    for i in range(start, start + count):
        u[i].dump(True)

listUtterances()

def objMethods(obj):
    out = filter(lambda k: True, obj.__class__.__dict__)
    out.sort()
    return out


def dumpSentences(lang):
    f   = file("/tmp/out_" + lang + ".txt", "w");
    div = 1000
    i   = 0

    for s in Sentence.objects.filter(language = lang):
        i += 1
        if not (i % div):
            print(str(i) + " sentences dumped")

        f.write(ja_enc(s.text))
        f.write("\n")

