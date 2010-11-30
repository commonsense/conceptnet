from csc.conceptnet.models import *
import codecs
activity, _ = Activity.objects.get_or_create(name='Pet game')
zh = Language.get('zh-Hant')
def run(filename):
    f = codecs.open(filename, encoding='utf-8')
    count = 0
    for line in f:
        if filename.endswith('1.txt') and count < 77600:
            count += 1
            continue
        line = line.strip()
        if not line: continue
        username, frame_id, text1, text2 = line.split(', ')
        user, _ = User.objects.get_or_create(username=username,
            defaults=dict(
                first_name='',
                last_name='',
                email='',
                password='-'
            )
        )
        frame = Frame.objects.get(id=int(frame_id))
        assert frame.language == zh
        try:
            got = RawAssertion.make(user, frame, text1, text2, activity)
            print got
        except RawAssertion.MultipleObjectsReturned:
            print "got multiple"
    f.close()

run('conceptnet_zh_part9.txt')
run('conceptnet_zh_part10.txt')
run('conceptnet_zh_api.txt')

