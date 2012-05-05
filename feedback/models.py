from django.db import models
from utils import fields
from django.core.exceptions import ValidationError
from imagekit.models import ImageModel
from datetime import datetime
from storage import upload_storage

# Create your models here.

class Feedback(models.Model):
    name = models.CharField(max_length=50,null=True,blank=True)
    email = models.EmailField("Email ID",null=True,blank=True)
    phone = models.CharField("Mobile", max_length=15,null=True,blank=True,validators=[fields.validate_phone])
    client = models.ForeignKey('accounts.Client', null=True,verbose_name = 'Acquired by',blank=True)
    feedback = models.TextField(error_messages={'required':"Please enter feedback/comments"})    
    type = models.CharField(max_length=25,blank=False,default='feedback',choices=(('feedback','Feedback'),('testimonial','Testimonial')))
    city = models.CharField(max_length=100,blank=True,null=True)
    submitted_on = models.DateTimeField(default=datetime.now())
    publish_it = models.BooleanField(default=False, help_text="Make this Feedback/Testimonial visible on WebSite")    

class CustomerImage(ImageModel):
    feedback = models.ForeignKey(Feedback)
    image = models.ImageField(upload_to='testimonial/%Y/%m/', storage=upload_storage)
    order = models.PositiveIntegerField(default=1)

    class IKOptions:
        # This inner class is where we define the ImageKit options for the model
        spec_module = 'feedback.specs'
        cache_dir = 'dp'
        image_field = 'image'

class ContactUs(models.Model):
    first_name = models.CharField("First Name",max_length=100,blank=False, error_messages={'required':"Please enter your First Name"})
    last_name = models.CharField("Last Name", max_length=100,blank=False, error_messages={'required':"Please enter your Last Name"})
    email = models.EmailField("Email ID",blank=False, error_messages={'required':"Please enter your Email ID",'invalid':"Please enter a valid Email ID"})
    phone = models.CharField("Contact No", max_length=10,blank=False,validators=[fields.validate_phone], error_messages={'required':'Please Enter Your Phone No.'})
    client = models.ForeignKey('accounts.Client', null=True,verbose_name = 'Acquired by',blank=True)
    comments = models.TextField('Your Comments',error_messages={'required':"Please enter Your Comments"})    
    subject = models.CharField(max_length=50,blank=False,default='general',
    choices=(
        ('general','General'),
        ('product_related','Product Related'),
        ('order_related',' Order Related'),
        ('payment_related','Payment Related'),
        ))
    submitted_on = models.DateTimeField(default=datetime.now())

    def __unicode__(self):
        return "%s %s - %s" %(self.first_name,self.last_name,self.subject)
