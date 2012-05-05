from django.db import models
import time

ACHOICELIST = ('Buy', 'Like', 'Feedback', 'Review', 'Rating')
STATUSLIST = ('Visible', 'Invisible')
ATYPECHOICES = [(i, i) for i in ACHOICELIST]
ASTATUSCHOICES = [(i,i) for i in STATUSLIST]

class Activity(models.Model):
    user = models.ForeignKey("users.Profile", blank=True, null=True)
    aclientdomain = models.ForeignKey("accounts.ClientDomain")
    atype = models.CharField(blank=False, choices=ATYPECHOICES, max_length=50)
    asrc = models.ForeignKey("catalog.SellerRateChart", blank=True, null=True)
    atime = models.PositiveIntegerField(default=int(time.time()))
    astream = models.CharField(max_length=200)
    astatus = models.CharField(
        choices=ASTATUSCHOICES, default='Visible', max_length=50
    )
