from csc_utils.batch import queryset_foreach
from conceptnet.models import Sentence, Assertion, RawAssertion

queryset_foreach(Assertion.objects.all(), lambda x: x.update_score(),
batch_size=100)
queryset_foreach(RawAssertion.objects.all(), lambda x: x.update_score(),
batch_size=100)
# queryset_foreach(Sentence.objects.exclude(language__id='en'), lambda x: x.update_score(), batch_size=100)

