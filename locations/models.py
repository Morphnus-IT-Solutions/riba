from django.db import models
from utils import fields 

# Create your models here.
class Country(models.Model):
    class Meta:
        verbose_name_plural = 'Countries'
    name = models.CharField(max_length=200, blank=True)

    type = models.CharField(max_length='15', db_index=True, default='primary',
            choices=(('primary','Primary'),('alternate','Alternate')))
    normalized = models.ForeignKey('self', blank=True, null=True,
            limit_choices_to={'type':'primary'})
    user_created = models.BooleanField(default=False, db_index=True)

    def __unicode__(self):
        return self.name

class State(models.Model):
    name = models.CharField(max_length=200, db_index=True, blank=True)
    #sap_code = models.CharField(max_length=4, null=True, blank=True) - removed - prady
    country = models.ForeignKey(Country)

    type = models.CharField(max_length='15', db_index=True, default='primary',
            choices=(('primary','Primary'),('alternate','Alternate')))
    normalized = models.ForeignKey('self', blank=True, null=True,
            limit_choices_to={'type':'primary'})
    user_created = models.BooleanField(default=False, db_index=True)

    def __unicode__(self):
        return self.name

class City(models.Model):
    class Meta:
        verbose_name_plural = 'Cities'
    name = models.CharField(max_length=200, db_index=True, blank=True)
    state = models.ForeignKey(State, blank=True, null=True)

    type = models.CharField(max_length='15', db_index=True, default='primary',
            choices=(('primary','Primary'),('alternate','Alternate')))
    normalized = models.ForeignKey('self', blank=True, null=True,
            limit_choices_to={'type':'primary'})
    user_created = models.BooleanField(default=False, db_index=True)

    def __unicode__(self):
        return self.name

class Pincode(models.Model):
    pincode = models.CharField(max_length=10)
    city = models.CharField(max_length=40)

class Address(models.Model):
    class Meta:
        verbose_name_plural = 'Addresses'

    address = models.TextField(blank=True)
    pincode = models.CharField(max_length=10,error_messages={'required':'Please enter pincode.'})

    city = models.ForeignKey(City, blank=True, null=True)
    state = models.ForeignKey(State, blank=True, null=True)
    country = models.ForeignKey(Country, blank=True, null=True)

    type = models.CharField(max_length=50, choices=(
        ('account','Account'),
        ('billing','Billing'),
        ('delivery','Delivery'),
        ('user','User')))

    profile = models.ForeignKey('users.Profile', null=True)
    account = models.ForeignKey('accounts.Account', null=True)

    created_on = models.DateTimeField(auto_now_add=True)
    uses = models.PositiveIntegerField(default=0)
    name = models.CharField(max_length=200, blank = True, null=True, error_messages={'required':'Please enter name.'})
    first_name = models.CharField(max_length=200,error_messages={'required':'Please enter first name.'})
    last_name = models.CharField(max_length=200,error_messages={'required':'Please enter last name.'})
    phone = models.CharField(max_length=100,error_messages={'required':'Please enter phone number.'})
    email = models.EmailField(blank=True, null=True)
    defaddress = models.BooleanField(default = False)

    def clone(self, save=False):
        cloned = Address()
        cloned.address = self.address
        cloned.pincode = self.pincode
        cloned.city = self.city
        cloned.state = self.state
        cloned.country = self.country
        cloned.type = self.type
        cloned.profile = self.profile
        cloned.account = self.account
        cloned.name = self.name
        cloned.first_name = self.first_name
        cloned.last_name = self.last_name
        cloned.phone = self.phone
        if save:
            cloned.save()
        return cloned

    def get_address_to_check(self):
        address_string = '%s%s%s%s%s%s%s%s' % (self.first_name, self.last_name, self.address, self.city, self.pincode, self.state, self.country, self.phone)
        expressions = [' ',',','-','.','/','#','(',')',"'",'"','\n','\r']
        for exp in expressions:
            address_string = address_string.replace(exp,'')

        return address_string

    def get_customer_address(self):
        address_string = '%s,%s,%s,%s,%s' % (self.address, self.city, self.pincode, self.state, self.country)
        #expressions = [' ',',','-','.','/','#','(',')',"'",'"','\n','\r']
        #for exp in expressions:
        #    address_string = address_string.replace(exp,'')

        return address_string

    def normalized_city(self):
        if self.city and self.city.normalized:
            return self.city.normalized
        return self.city

    def normalized_state(self):
        if self.state and self.state.normalized:
            return self.state.normalized
        return self.state

    def normalized_country(self):
        if self.country and self.country.normalized:
            return self.country.normalized
        return self.country

    def address_hash(self):
        hash = self.address.lower()
        return hash

    def is_same_as(self, address):
        if self.normalized_country() and address.normalized_country():
            if self.normalized_country().id != address.normalized_country().id:
                return False
        if self.normalized_state() and address.normalized_state():
            if self.normalized_state().id != address.normalized_state().id:
                return False
        if self.normalized_city() and address.normalized_city():
            if self.normalized_city().id != address.normalized_city().id:
                return False
        if self.pincode != address.pincode:
            return False
        if self.address_hash() != address.address_hash():
            return False
        return True

    def toString(self):
        return '%s\n%s\n%s\n%s-%s\n%s\n%s\nPhone:%s' % (self.first_name, self.last_name, self.address, self.city, self.pincode, self.state, self.country, self.phone)

    def __unicode__(self):
        return '%s, %s, %s, %s, %s, %s, %s, %s, %s' % (self.first_name, self.last_name, self.address, self.city, self.state, self.country, self.pincode, self.phone, self.email)

class AddressBook(models.Model):
    address = models.TextField(blank=True)
    pincode = models.CharField(max_length=10,error_messages={'required':'Please enter pincode.'}, validators=[fields.validate_pincode])

    city = models.ForeignKey(City, blank=True, null=True)
    state = models.ForeignKey(State, blank=True, null=True)
    country = models.ForeignKey(Country, blank=True, null=True)

    profile = models.ForeignKey('users.Profile', null=True)
    name = models.CharField(max_length=200, blank=True, null=True, error_messages={'required':'Please enter name.'})
    first_name = models.CharField(max_length=200,error_messages={'required':'Please enter first name.'})
    last_name = models.CharField(max_length=200,error_messages={'required':'Please enter last name.'})

    phone = models.CharField(max_length=100,error_messages={'required':'Please enter phone number.'}, validators=[fields.validate_phone])
    email = models.EmailField(null=True, blank=True)

    defaddress = models.BooleanField(default = False)

    def clone(self, save=False):
        cloned = Address()
        cloned.address = self.address
        cloned.pincode = self.pincode
        cloned.city = self.city
        cloned.state = self.state
        cloned.country = self.country
        cloned.profile = self.profile
        cloned.name = self.name
        cloned.first_name = self.first_name
        cloned.last_name = self.last_name
        cloned.phone = self.phone
        cloned.email = self.email
        if save:
            cloned.save()
        return cloned
    def toString(self):
        return '%s\n%s\n%s\n%s-%s\n%s\n%s\nPhone:%s' % (self.first_name, self.last_name, self.address, self.city, self.pincode, self.state, self.country, self.phone)

    def get_address_to_check(self):
        address_string = '%s%s%s%s%s%s%s%s' % (self.first_name, self.last_name, self.address, self.city, self.pincode, self.state, self.country, self.phone)
        expressions = [' ',',','-','.','/','#','(',')',"'",'"','\n','\r']
        for exp in expressions:
            address_string = address_string.replace(exp,'')

        return address_string

    def __unicode__(self):
        return '%s, %s, %s, %s, %s, %s, %s, %s, %s' % (self.first_name, self.last_name, self.address, self.city, self.state, self.country, self.pincode, self.phone, self.email)
