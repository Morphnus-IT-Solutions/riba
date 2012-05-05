from django.db import models
from tinymce.models import HTMLField
from south.modelsinspector import add_introspection_rules
add_introspection_rules([],["^tinymce\.models\.HTMLField"])

# Create your models here.
class Help(models.Model):
    heading = models.CharField(max_length=500)
    slug = models.SlugField(unique=True, db_index=True)
    help = HTMLField(blank=True)
