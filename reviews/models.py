from django.db import models
from datetime import datetime
# Create your models here.
class Review(models.Model):
    title = models.CharField(max_length=500)
    review = models.TextField()
    rating = models.IntegerField(default=1,choices=(
            (1,1),
            (2,2),
            (3,3),
            (4,4),
            (5,5)))
    display_name = models.CharField(max_length=200,blank=True,null=True)
    product = models.ForeignKey('catalog.Product')
    rate_chart = models.ForeignKey('catalog.SellerRateChart')
    user = models.ForeignKey('users.Profile')
    status = models.CharField(db_index=True, default='new', max_length=15, choices=(
            ('new','New'),
            ('flagged', 'Flagged'),
            ('approved', 'Approved'),
            ('removed','Removed')))
    reviewed_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True, default=datetime.now())
    no_helpful = models.IntegerField(null=False, default=0)
    no_not_helpful = models.IntegerField(null=False, default=0)
    reviewed_by = models.CharField(max_length=200)
    avg_review_rating = models.FloatField(default=0)
    review_rating_user = models.ManyToManyField('users.Profile',blank=True, null=True,related_name='rating_user')  
    total_review_ratings=models.IntegerField(default=0)

    def __unicode__(self):
        return self.title

class ReviewHelpfulness(models.Model):
    review = models.ForeignKey(Review)
    status = models.CharField(max_length=15, choices=(
            ('not_helpful', 'Not Helpful'),
            ('helpful', 'Helpful'),
            ('abusive', 'Abusive')))
    user = models.ForeignKey('users.Profile')
