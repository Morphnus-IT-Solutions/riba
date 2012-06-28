from django.db import models
from categories.models import Category
from question.models import Question, Field
from tinymce.models import HTMLField
from south.modelsinspector import add_introspection_rules
from storage import upload_storage

add_introspection_rules([],["^tinymce\.models\.HTMLField"])

# Create your models here.
class Template(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    category = models.ForeignKey(Category,verbose_name='Category', db_index=True)
    upload_document = models.FileField(upload_to='template/%Y/%m', storage=upload_storage,blank=True,null=True)
    upload_text = HTMLField(blank = True, null = True)
    list_price = models.DecimalField(max_digits=10, decimal_places=2,
            null=True, verbose_name='List Price')
    offer_price = models.DecimalField(max_digits=10, decimal_places=2,
            null=True, verbose_name='Price', db_index=True)
    time_to_build = models.IntegerField(default=0, verbose_name="Time to Build (in minutes)")
    state = models.CharField(max_length=20, blank=True, default='new', verbose_name='State', choices=(
        ('new','New'),
        ('draft','Draft'),
        ('submitted','Submitted')), db_index=True)
    information = HTMLField(blank = True, null = True, verbose_name="Information about how to use the document")
    about = HTMLField(blank = True, null = True, verbose_name="What is in the document?")

    def __unicode__(self):
        return self.title

class Keyword(models.Model):
    template = models.ForeignKey(Template, db_index=True)
    keyword = models.CharField(max_length=100, db_index=True)

    class Meta:
        unique_together = ('template', 'keyword', )

    def __unicode__(self):
        return self.keyword


class Questionnaire(models.Model):
    template = models.ForeignKey(Template)
    question = models.ForeignKey(Question, db_index=True)
    keyword = models.ForeignKey(Keyword, blank=True, null=True)
    field = models.ForeignKey(Field, blank=True, null=True)
    mandatory = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=1)

    def __unicode__(self):
        return "%s - %s" % (self.question, self.keyword)
