from django.db import models
from storage import upload_storage
from lists.models import List


# Create your models here.

class MenuItem(models.Model):
    class Meta:
        unique_together = ('parent','sort_order')
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=25, default='category', choices=(
        ('category','Category'),
        ('store','Store'),
        ('custom','Custom')))
    filters = models.TextField(blank=True)
    parent = models.ForeignKey('self', blank=True,null=True)
    sort_order = models.PositiveIntegerField()

    category = models.ForeignKey('categories.Category', blank=True, null=True)
    store = models.ForeignKey('categories.Store', blank=True, null=True)
    url = models.CharField(max_length=500, blank=True)

    def __unicode__(self):
        return self.name


class Announcements(models.Model):
    title = models.CharField(max_length=1000,blank=True)
    text = models.CharField(max_length=1000)
    landing_page_url = models.URLField(verify_exists=False)
    starts_on = models.DateTimeField()
    ends_on = models.DateTimeField()
    domain = models.ForeignKey('accounts.ClientDomain')
    sort_order = models.IntegerField(default=0)

    def __unicode__(self):
        return self.text


class Banner(models.Model):
	name = models.CharField(max_length=500)
	tagline = models.CharField(max_length=1000, blank=True, null=True)
	image = models.ImageField(blank=True, null=True, upload_to='banner/%Y/%m', storage=upload_storage)
	client = models.ForeignKey('accounts.Client')
	sort_order = models.PositiveIntegerField(default=1)
	redirect_to = models.CharField(max_length=200, blank=True, null=True)    
	type = models.CharField(max_length=50, choices=(
		('image_mapping', 'Image Mapping'),
		('direct_link', 'Direct Link'),
		),
		default='direct_link')
	 
	def __unicode__(self):
		return '%s-%s' % (self.name, self.client)

class Coordinates(models.Model):
	list=models.ForeignKey('lists.List', blank=True, null=True)
	sequence = models.PositiveIntegerField(blank=True, null=True, default=1)
 	co_ordinates = models.CharField(max_length=500, blank=True, null=True)
	link = models.CharField(max_length=1000, blank=True, null=True)
