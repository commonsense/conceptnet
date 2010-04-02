# -*- coding: utf-8 -*-
from csc.conceptnet4.models import *

def test_chinese():
    zh = Language.get('zh-Hant')
    railway = u"迪士尼线"
    assert zh.nl.normalize(railway) == railway
