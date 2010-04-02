from csc.conceptnet4.models import *
import codecs
zh = Language.get('zh-Hant')
activity = Activity.objects.get(name='Pet game')

def run(filename):
    f = codecs.open(filename, encoding='utf-8')
    for line in f:
        line = line.strip()
        if not line: continue
        username, frame_id, text1, text2 = line.split(',')
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
        got = RawAssertion.make(user, frame, text1, text2, activity)
        print got
    f.close()

run('conceptnet_zh_part2.txt')
