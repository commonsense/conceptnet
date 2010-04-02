from csc.conceptnet4.models import *
from django.db import transaction

def nerf(user):
    for vote in Vote.objects.filter(user=user):
        badass = vote.object
        vote.delete()
        badass.update_score()
        print badass

@transaction.commit_on_success
def nerf_bobman():
    bobman = User.objects.get(username='bobMan')
    crap = bobman.rawassertion_set.all()[0]
    lusers = [vote.user for vote in crap.votes.all() if vote.vote == 1]
    
    for luser in lusers:
        print
        print luser
        nerf(luser)
        
if __name__ == '__main__': nerf_bobman()