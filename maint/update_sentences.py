from csc.util import queryset_foreach
from csc.corpus.models import Sentence

queryset_foreach(Sentence.objects.filter(id__lt=1367900).order_by('-id'),
  lambda x: x.update_consistency(),
  batch_size=100)

