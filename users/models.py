from django.db import models
from utils.fields import PhoneNumberField
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from accounts.models import Account, Client, ClientDomain
from storage import upload_storage
from django.core.validators import RegexValidator
from utils import fields
from datetime import datetime
from locations.models import Address, AddressBook
import hashlib

class UserTag(models.Model):
    tag = models.CharField(max_length=200, unique=True)
    type = models.CharField(max_length=25)

    def __unicode__(self):
        return self.tag

class Profile(models.Model):
    # which user does this profile belong to
    user = models.ForeignKey(User)

    full_name = models.CharField("Name", max_length=150, blank=True)
    primary_phone = models.CharField("Mobile", max_length=15, blank=True, validators=[fields.validate_phone])
    secondary_phone = models.CharField("Alternate Phone", max_length=15, blank=True, validators=[RegexValidator(r'^[0-9]{10,15}$',message='Enter a valid Alternate Phone number.')])
    primary_email = models.EmailField("Email ID", blank=True)
    secondary_email = models.EmailField(blank=True,)
    verify_code = models.IntegerField(blank=True, null=True)
    verification_code = models.CharField(max_length = 50, blank = True, null=True)
    is_verified = models.BooleanField(default=False)
    transaction_password = models.CharField(blank=True, null=True, max_length=20)
    gender = models.CharField(blank=False, default='m', choices=(
        ('m','Male'),('f','Female')), max_length=1)
    date_of_birth = models.DateField("Date of Birth", null=True, blank=True)
    salutation = models.CharField(blank=True, choices=(
        ('mr','Mr.'),('miss','Ms.'),('mrs','Mrs.'),('ms','Messrs')),
        max_length=15)

    buyer_or_seller = models.CharField(max_length=100, default='Buyer', choices=(
        ('Buyer','Buyer'),
        ('Seller', 'Seller'),
        # TODO This is a pollution here. See if this can be discared.
        ('Deleted', 'Deleted'),
        ('Both','Both')))
    is_agent  = models.BooleanField(default=False)
    # if the user is a buyer, then her account association data
    acquired_through_account = models.ForeignKey('accounts.Account', null=True,
        verbose_name = 'Acquired by',
        blank=True, related_name='owned_customers')
    customer_of_accounts = models.ManyToManyField('accounts.Account', null=True,
        verbose_name = 'Customer of',
        blank=True, related_name='customers')
    # if the user is a seller, then the account data
    managed_accounts = models.ManyToManyField('accounts.Account', null=True,
        blank=True, related_name='account_staff')

    marketing_alerts = models.CharField(max_length=25, default='neutral', choices=(
        ('neutral','Neutral'),
        ('yes','Yes'),
        ('no','No')))

    salt = models.CharField(max_length=36, blank=True)
    passcode = models.CharField(max_length=36, blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(UserTag, blank=True, null=True)

    #new fields created for the /user/profile page
    webpage = models.CharField(max_length=200,blank=True)
    facebook = models.CharField("Facebook URL", max_length=200,blank=True)
    twitter = models.CharField("Twitter URL", max_length=200,blank=True)
    email_notification = models.BooleanField(default=0)
    sms_alert = models.BooleanField(default = 0)

    #new fields created for the FB Lists page
    profession = models.CharField(max_length=200, null=True, blank=True)
    user_photo = models.ImageField(blank=True, null=True,
            upload_to='user/%Y/%m', storage=upload_storage)

    atg_username = models.CharField(max_length=200, blank=True, null=True, unique=True)
    atg_login = models.CharField(max_length=40, blank=True, null=True, unique=True)
    atg_password = models.CharField(max_length=35, blank=True, null=True)

    cod_status = models.CharField(max_length=25, default='neutral', choices=(
        ('neutral','Neutral'),
        ('whitelisted','Whitelisted'),
        ('blacklisted','Blacklisted')))
    
    #Exceptions
    
    def __unicode__(self):
        return self.full_name or self.primary_phone

    def check_atg_password(self, password):
        if not password:
            return False
        return self.atg_password == hashlib.md5(password.encode(
            'ascii','ignore')).hexdigest()

    def get_primary_emails(self):
        emails = Email.objects.filter(user=self)
        return emails

    def get_primary_phones(self):
        phones = Phone.objects.filter(user=self,type='primary')
        return phones

    def get_phone(self):
        if self.primary_phone:
            return self.primary_phone
        else:
            phones = Phone.objects.filter(user=self)
            if phones:
                phone = phones[0]
                phone_phone =  phone.phone
                return phone_phone
            else:
                return None

    def get_email(self):
        if self.primary_email:
            return self.primary_email
        else:
            emails = Email.objects.filter(user=self)
            if emails:
                email = emails[0]
                email_email =  email.email
                return email_email
            else:
                return None

    _clients = None
    def managed_clients(self):
        if self._clients:
            return self._clients 
        clients=[]
        for account in self.managed_accounts.select_related('client').all():
            if account.client not in clients:
                clients.append(account.client)
        self._clients = clients
        return clients
    
    def get_addresses(self, request, **kwargs):
        client = kwargs.get('client', None)
        user_addresses = AddressBook.objects.filter(profile=self).order_by('-id')[:3]
        valid_user_addresses = []
        for address in user_addresses:
            if not address.address:
                continue
            elif not address.state:
                continue
            elif not address.city:
                continue
            elif not address.state.name in fbapiutils.STATES_MAP:
                continue
            elif not address.pincode:
                continue
            else:
                valid_user_addresses.append(address)
        return valid_user_addresses
   
    def check_address_present(self, request, **kwargs):
        address = kwargs.get('address')
        user_all_addresses = AddressBook.objects.filter(profile=self)
        present = False
        for user_address in user_all_addresses:
            present = True
            if user_address.address.lower() != address.address.lower():
                present = False
            if user_address.city.name.lower() != address.city.name.lower():
                present = False
            if user_address.state.name.lower() != address.state.name.lower():
                present = False
            if user_address.pincode.lower() != address.pincode.lower():
                present = False
            if user_address.first_name.lower() != address.first_name.lower():
                present = False
            if user_address.last_name.lower() != address.last_name.lower():
                present = False
            if present == True:
                break
        return present

    def add_address(self, request, **kwargs):
        address = kwargs.get('address')
        address_present = self.check_address_present(request, address=address)
        if not address_present:
            address_book = AddressBook()
            address_book.profile = self
            address_book.address = address.address
            address_book.pincode = address.pincode
            address_book.city = address.city
            address_book.state = address.state
            address_book.country = address.country
            address_book.name  = address.name
            address_book.first_name = address.first_name
            address_book.last_name = address.last_name
            address_book.phone = address.phone
            address_book.email = address.email
            address_book.save()

class Email(models.Model):
    email = models.EmailField("Email ID",unique=True)
    cleaned_email = models.CharField(max_length=100, default=None, blank=True, null=True, unique=True)
    user = models.ForeignKey(Profile)
    type = models.CharField(max_length=15,db_index=True,choices=(
        ('primary','Primary'),
        ('secondary','Secondary'),
        ('subscription','Subscription')))
    is_verified = models.BooleanField(default=False)
    verified_on = models.DateTimeField(blank=True, null=True)
    verification_code = models.CharField(max_length = 50, blank = True, null=True)

    def __unicode__(self):
        return self.email

class Phone(models.Model):
    phone = models.CharField("Mobile", max_length=15,unique=True)
    user = models.ForeignKey(Profile)
    type = models.CharField(max_length=15,db_index=True, choices=(
        ('primary','Primary'),
        ('secondary','Secondary'),
        ('subscription','Subscription')))
    is_verified = models.BooleanField(default=False)
    verified_on = models.DateTimeField(blank=True, null=True)
    verification_code = models.CharField(max_length = 50, blank = True, null=True, db_index=True)
    def __unicode__(self):
        return self.phone

class NewsLetter(models.Model):
    client = models.ManyToManyField(Client)
    newsletter = models.CharField(max_length = 100)
    affiliate_name = models.CharField(max_length = 100, blank = True, null=True)
    affiliate_logo = models.ImageField(upload_to = 'images/logos/', storage=upload_storage,blank = True,null = True)
    affiliate_text = models.CharField(max_length = 300, blank = True, null = True)
    def __unicode__(self):
        
        return '%s-%s' % (self.newsletter,self.client)

class ShoppingPage(models.Model):
    redirect_page = models.URLField()
    newsletter = models.ForeignKey(NewsLetter)
    image = models.ImageField(upload_to = 'images/logos/', storage=upload_storage)

class DailySubscription(models.Model):
    newsletter = models.ForeignKey(NewsLetter)
    source = models.CharField(max_length = 500,blank=True,null=True)
    email_alert_on = models.ForeignKey(Email,blank=True,null=True)
    is_email_alert = models.BooleanField(default=True)
    sms_alert_on = models.ForeignKey(Phone,blank=True,null=True)
    is_sms_alert = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    last_modified_date = models.DateTimeField(auto_now=True, default = datetime.now())
    verified_on = models.DateTimeField(blank=True, null=True)
    verification_code = models.CharField(max_length = 100, blank = True, null=True)

class PpdAdminUser(models.Model):
    profile = models.ForeignKey(Profile)
    accounts = models.ManyToManyField(Account)

    _clients = None
    def managed_clients(self):
        if self._clients:
            return self._clients 
        clients=[]
        for account in self.accounts.all():
            if account.client not in clients:
                clients.append(account.client)
        self._clients = clients
        return clients

    def save(self, *args, **kwargs):
        super(PpdAdminUser,self).save(*args,**kwargs)
        self._clients = None
        self.managed_clients()

class Subscription(models.Model):
    client = models.ForeignKey('accounts.Client', blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=25, blank=True, null=True)
    newsletter = models.ForeignKey(NewsLetter)
    contact_type = models.CharField(max_length=10, default="email", choices=(
            ('email','Email'),
            ('phone','Phone')))
    contact = models.CharField(max_length=200)
    subscribed_on = models.DateTimeField(auto_now_add=True)
    verified_on = models.DateTimeField(blank=True, null=True)
    verification_code = models.CharField(max_length = 50, blank = True, null=True)
    modified_on = models.DateTimeField(auto_now=True)
    subscription_alert = models.BooleanField(default=True)
    
    def __unicode__(self):
        return "%s Subscribed on domain: %s at %s" % (self.contact, self.source, self.subscribed_on)

    class Meta:
        unique_together = ('contact', 'newsletter')


class Permission(models.Model):
    user = models.ForeignKey(User)
    system = models.CharField(max_length=20, blank=False, null=False,
        choices=(('rms','RMS'),
        ('platform','Platform'),
        ('cs','CS'),
        ('analytics','Analytics')))
    
    #Adding a generic foreign key using ContentType. The fields content_type, object_id and content_object
    #together form a generic foreign key relationship. Do not modify any one of these.
    content_type = models.ForeignKey(ContentType, related_name='+')
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ('user','system','object_id')

class FacebookInfo(models.Model):
    email = models.ForeignKey('users.Email', db_index=True)
    is_new_email = models.BooleanField(default=False)
    facebook_id = models.CharField(max_length=50, unique=True)
    linking_done = models.BooleanField(default=False)
    linking_denied = models.BooleanField(default=False)
    linked_to = models.CharField(max_length=200, default='')

    def __unicode__(self):
        return '%s, %s' % (self.email, self.facebook_id)

class UserMerges(models.Model):
    user = models.ForeignKey('users.Profile')
    email = models.ForeignKey('users.Email', blank=True, null=True)
    phone = models.ForeignKey('users.Phone', blank=True, null=True)
    merged_to = models.ForeignKey('users.Profile', related_name='+')

    class Meta:
        unique_together = ('user', 'email', 'phone', 'merged_to')

class FacebookAppScore(models.Model):
    facebook_user = models.CharField(max_length=100, db_index=True)
    facebook_name = models.CharField(max_length=100, blank=True,
        null=True, default='')
    score = models.IntegerField(default=0)

class Tab(models.Model):
    tab_name = models.CharField(max_length=30)
    system = models.CharField(max_length=20, blank=False, null=False,
        choices=(('rms','RMS'),
        ('platform','Platform'),
        ('cs','CS'),
        ('analytics','Analytics')))

    def __unicode__(self):
        return '%s - %s' % (self.tab_name, self.system)

class UserTab(models.Model):
    tab = models.ForeignKey(Tab)
    user = models.ForeignKey(Profile, db_index=True, related_name='tabs')
    
    def __unicode__(self):
        return '%s - %s' % (self.tab, self.user)

class ProfileRemap(models.Model):
    email = models.ForeignKey('Email', null=True, blank=True)
    phone = models.ForeignKey('Phone', null=True, blank=True)
    old_profile = models.ForeignKey('Profile', related_name='oldprofiles')
    new_profile = models.ForeignKey('Profile')
