from django.db import models
from utils.fields import PhoneNumberField
from django.contrib.auth.models import User
from django.conf import settings
from payouts.models import *
from accounts.models import *
from django.core.cache import cache


class Client(models.Model):
    name = models.CharField(max_length=100)
    slug=models.CharField(max_length=100, null=True, blank=True)
    # order email settings
    confirmed_order_email = models.CharField(max_length=500,default='<Chaupaati Bazaar> order@chaupaati.com')
    pending_order_email = models.CharField(max_length=500,default='<Chaupaati Bazaar> lead@chaupaati.com')
    noreply_email = models.CharField(max_length=200,default='<Chaupaati Bazaar> noreply@chaupaati.com')
    feedback_email = models.CharField(max_length=200,default='<Chaupaati Bazaar> feedback@chaupaati.com')
    promotions_email = models.CharField(max_length=200,default='<Chaupaati Bazaar> promotions@chaupaati.com')
    signature = models.TextField()
    terms_and_conditions = models.TextField()
    pending_order_helpline = models.CharField(max_length=25, default='0-922-222-1947')
    confirmed_order_helpline = models.CharField(max_length=25,default='0-922-222-1947')
    clientdomain_name = models.CharField(max_length=100, null=True,blank=True)
    #smtp and sms settings
    sms_mask = models.TextField(blank=True)
    
    #order_prefix
    order_prefix = models.CharField(max_length=5, blank=True, null=True, default='')

    def __unicode__(self):
        return self.name

    def get_noreply_from_address(self):
        return "%s<%s@%s>" % (self.name, 'noreply', self.clientdomain_name)

    def get_lead_from_address(self):
        return "%s<%s@%s>" % (self.name, 'lead', self.clientdomain_name)

    def get_order_from_address(self):
        return "%s<%s@%s>" % (self.name, 'order', self.clientdomain_name)

    def get_share_from_address(self):
        return "%s<%s@%s>" % (self.name, 'share', self.clientdomain_name)
        
    def get_payment_options(self):
        choice_list = []
        choices = ()
        for p in DomainPaymentOptions.objects.select_related('payment_option', 'payment_option__payment_mode').filter(payment_option__client = self, is_active=True):
            choice = (p.payment_option.payment_mode.code, p.payment_option.payment_mode.name)
            if not choice in choice_list:
                choices += (choice,)
                choice_list.append(choice)
        return choices
        
            
class ClientDomain(models.Model):
    domain = models.CharField(max_length=150)
    code = models.CharField(max_length=10)
    client = models.ForeignKey(Client)
    type = models.CharField(max_length=25, default='website',choices=(
        ('website','Website'),
        ('cc','Call Center'),
        ('support','Support'),
        ('reports','Reports')))
    default_redirect_to = models.CharField(max_length=50,blank=True)
    is_public = models.BooleanField(default=True)
    is_channel = models.BooleanField(default=True)
    custom_home_page = models.CharField(max_length=100, default='web/home/home.html')
    sale_pricelist = models.CharField(max_length=15, blank=True)
    list_pricelist = models.CharField(max_length=15, blank=True)


    def __unicode__(self):
        return self.domain
    
    def get_sale_pricelist(self):
        if self.sale_pricelist:
            return self.sale_pricelist
        else:
            return self.client.get_sale_pricelist()

    def get_list_pricelist(self):
        if self.list_pricelist:
            return self.list_pricelist
        else:
            return self.client.get_list_pricelist()

class Account(models.Model):
    class Meta:
        permissions = (
            ('can_fulfil_order','Can fulfil order'),
            ('can_cancel_order','Can cancel order'),
            ('can_manage_catalog','Can manage catalog'),
            ('can_manage_offers','Can manage offers'),
            ('can_manage_customers','Can manage customers'),
        )

    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=200, null=False, blank=False)
    client = models.ForeignKey(Client)
    code = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    is_exclusive = models.BooleanField(default=False)

    # order email settings
    confirmed_order_email = models.CharField(max_length=500,default='<Chaupaati Bazaar> order@chaupaati.com')
    pending_order_email = models.CharField(max_length=500,default='<Chaupaati Bazaar> lead@chaupaati.com')
    share_product_email = models.CharField(max_length=500,default='<Chaupaati Bazaar> share@chaupaati.com')
    signature = models.TextField()
    pg_return_url = models.URLField(blank=True,default=settings.TINLA_URL, verify_exists=False)
    pending_order_helpline = models.CharField(max_length=25, default='0-922-222-1947')
    confirmed_order_helpline = models.CharField(max_length=25,default='0-922-222-1947')
    
    #smtp and sms settings
    sms_mask = models.TextField(blank=True)

    # account type
    type = models.CharField(max_length=100, default='Channel', choices=(
        ('Brand','Brand'),
        ('Channel','Channel'),
        ('Dealer','Dealer'),
        ('Retailer','Retailer')))

    # contact info
    customer_support_no = models.CharField(max_length=150, blank=True)

    primary_phone = models.CharField(max_length=15, blank=True)
    secondary_phone = models.CharField(max_length=15, blank=True)

    primary_email = models.CharField(max_length=500,blank=True)
    secondary_email = models.CharField(max_length=500, blank=True)

    # policies
    shipping_policy = models.TextField(blank=True)
    returns_policy = models.TextField(blank=True)
    tos = models.TextField(blank=True)

    dni = models.CharField(max_length=5,blank=True)
    greeting_title = models.TextField(blank=True)
    greeting_text = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    def get_notication_email_addresses(self, event):
        ns_set = self.notificationsettings_set.filter(event=event)
        if ns_set:
            ns = ns_set[0]
            emails = ''
            if ns.on_primary_email and self.primary_email:
                emails += self.primary_email
            if ns.on_secondary_email and self.secondary_email:
                if emails:
                    emails += "," + self.secondary_email
                else:
                    emails += self.secondary_email
            return emails
        return ''

    def get_general_notification_email_addresses(self):
        return self.get_notication_email_addresses('general')

    def get_pending_order_notification_email_addresses(self):
        return self.get_notication_email_addresses('pending_order_event')

    def get_confirmed_order_notification_email_addresses(self):
        return self.get_notication_email_addresses('order_confirmed_event')

    def save(self, *args, **kwargs):
        super(Account,self).save(*args, **kwargs)
        try:
            sc = SellerConfigurations.objects.get(seller = self)
        except:
            sc = SellerConfigurations(seller=self)
            sc.save()
    
class NotificationSettings(models.Model):
    account = models.ForeignKey(Account)
    GENERAL_NOTIFICATION_EVENT = 'general'
    PENDING_ORDER_EVENT = 'pending_order_event'
    ORDER_CONFIRMED_EVENT = 'order_confirmed_event'
    
    EVENT_CHOICES = ( 
        (GENERAL_NOTIFICATION_EVENT, 'General'),
        (PENDING_ORDER_EVENT, 'Pending Order'),
        (ORDER_CONFIRMED_EVENT, 'Cofirmed Order'))
    event = models.CharField(max_length=100, choices=EVENT_CHOICES, default="Select notification event")
    on_primary_email = models.BooleanField(default=True)
    on_secondary_email = models.BooleanField(default=False)

    on_primary_phone = models.BooleanField(default=False)
    on_secondary_phone = models.BooleanField(default=False)

class Feed(models.Model):
    account = models.ForeignKey(Account)
    feed_url = models.URLField(blank=True)
    feed_file_type = models.CharField(max_length=3,choices=(
        ('xml','XML'),
        ('xls','XLS')))
    sync_type = models.CharField(max_length=10,choices=(
        ('auto','Auto'),
        ('manual','Manual')))
    last_sync_date = models.DateTimeField(blank=True)


class PaymentGroups(models.Model):
    name = models.CharField(max_length=25)
    code = models.CharField(max_length=25)

    def __unicode__(self):
        return '%s' %self.name

class PaymentMode(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=25)
    client = models.ForeignKey(Client, null=True, blank=True)
    is_grouped = models.BooleanField(default=False)
    group_code = models.CharField(max_length=25,blank=True, null=True)
    group_name = models.CharField(max_length=25, null=True, blank=True)
    service_provider = models.CharField(max_length=25,blank=True, null=True)
    group = models.ForeignKey(PaymentGroups, null=True, blank=True)
    validate_billing_info = models.BooleanField(default=False)
    service_provider = models.CharField(max_length=25, blank=True)

    def __unicode__(self):
        if self.client:
            return '%s-%s' % (self.name,self.client)
        else:
            return '%s' % (self.name)


class PaymentOption(models.Model):
    class Meta:
        unique_together = ('account','sort_order')

    account = models.ForeignKey(Account,blank=True,null=True)
    #seller_rate_chart = models.ManyToManyField('catalog.SellerRateChart',blank=True,null=True,limit_choices_to={'stock_status':'instock','product__status':'active','seller__client__id':5})
    payment_mode = models.ForeignKey(PaymentMode, null=True, blank=True)
    client = models.ForeignKey(Client, blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    is_instant = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    is_noninstant = models.BooleanField(default=False)
    is_offline = models.BooleanField(default=False)
    complete_order_url = models.CharField(max_length=200, null=True, blank=True) 
    in_favor_of = models.CharField(max_length=300,blank=True, null=True)
    payment_delivery_address = models.TextField(blank=True, null=True)
    bank_ac_no = models.CharField(max_length=50,blank=True,verbose_name='Bank account number', null=True)
    bank_ac_type = models.CharField(max_length=100,blank=True,default='current',verbose_name='Bank account type',choices=(
        ('current', 'Current'),
        ('saving', 'Saving')))
    bank_ac_name = models.CharField(max_length=200,blank=True,verbose_name='Bank account name', null=True)
    bank_name = models.CharField(max_length=300,blank=True, null=True)
    bank_branch = models.CharField(max_length=300,blank=True, null=True)
    bank_address = models.TextField(blank=True, null=True)
    bank_ifsc = models.CharField(max_length=100,blank=True,verbose_name='Bank IFSC code', null=True)
    location_url = models.CharField(max_length=300,blank=True, null=True)
    #cod_locations

    
    def __unicode__(self):
        if self.client:
            return '%s (%s)' % (self.payment_mode, self.client)
        return '%s (%s)' % (self.payment_mode, self.account.name)

class DomainPaymentOptions(models.Model):
    payment_option = models.ForeignKey(PaymentOption)
    client_domain = models.ForeignKey(ClientDomain)
    is_active = models.BooleanField(default=False)
    is_dynamic_pm_active = models.BooleanField(default=False)
    order_taking_option = models.CharField(max_length='20', default='book',choices=(
                    ('book','Book'),
                    ('book_and_confirm','Book and Confirm')))


    def __unicode__(self):
        return self.client_domain.domain

class PaymentGateways(models.Model):
    payment_mode = models.ForeignKey(PaymentMode)
    name = models.CharField(max_length=25)
    code = models.CharField(max_length=50)
    card_active = models.BooleanField(default=True)
    card_emi_active = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s %s' %(self.name, self.code)

class DepositPaymentOptions(models.Model):
    class Meta:
        unique_together = ('client', 'bank_name',)

    payment_mode = models.ForeignKey(PaymentMode)
    client = models.ForeignKey(Client)
    is_active = models.BooleanField(default=True)
    bank_ac_no = models.CharField(max_length=50, verbose_name='Bank account number')
    bank_ac_type = models.CharField(max_length=100,default='current',verbose_name='Bank account type',choices=(
        ('current', 'Current'),
        ('saving', 'Saving')))
    bank_ac_name = models.CharField(max_length=200,verbose_name='Bank account name')
    bank_name = models.CharField(max_length=300)
    bank_ifsc = models.CharField(max_length=100,verbose_name='Bank IFSC code')

    def __unicode__(self):
        return '%s, %s' % (self.client, self.bank_ac_name)
