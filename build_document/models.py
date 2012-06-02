from django.db import models
from categories.models import Category
from tinymce.models import HTMLField
from south.modelsinspector import add_introspection_rules
from storage import upload_storage

add_introspection_rules([],["^tinymce\.models\.HTMLField"])

# Create your models here.
class Template(models.Model):
    title = models.CharField(max_length=500)
    category = models.ForeignKey('categories.Category',verbose_name='Category')
    upload_document = models.FileField(upload_to='template/%Y/%m', storage=upload_storage,blank=True,null=True)
    upload_text = HTMLField(blank = True, null = True)
    list_price = models.DecimalField(max_digits=10, decimal_places=2,
            null=True, verbose_name='List Price')
    offer_price = models.DecimalField(max_digits=10, decimal_places=2,
            null=True, verbose_name='Price')
    time_to_build = models.IntegerField(default=0, verbose_name="Time to Build (in minutes)")
    state = models.CharField(max_length=20, blank=True, default='new', verbose_name='State', choices=(
        ('new','New'),
        ('draft','Draft'),
        ('final','Final')))
    information = HTMLField(blank = True, null = True)
    about = HTMLField(blank = True, null = True)
