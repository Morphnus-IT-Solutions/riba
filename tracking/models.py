from django.db import models

class ViewUsage(models.Model):
    client_domain = models.ForeignKey('accounts.ClientDomain', db_index=True) 
    session = models.CharField(max_length=32, db_index=True)
    user = models.ForeignKey('users.Profile', db_index=True, null=True,
        blank=True)
    product = models.ForeignKey('catalog.Product', db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

class LikeUsage(models.Model):
    client_domain = models.ForeignKey('accounts.ClientDomain', db_index=True) 
    session = models.CharField(max_length=32, db_index=True)
    user = models.ForeignKey('users.Profile', db_index=True, null=True,
        blank=True)
    product = models.ForeignKey('catalog.Product', db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

class AddToCartUsage(models.Model):
    client_domain = models.ForeignKey('accounts.ClientDomain', db_index=True) 
    session = models.CharField(max_length=32, db_index=True)
    user = models.ForeignKey('users.Profile', db_index=True, null=True,
        blank=True)
    product = models.ForeignKey('catalog.Product', db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

class BookUsage(models.Model):
    client_domain = models.ForeignKey('accounts.ClientDomain', db_index=True) 
    session = models.CharField(max_length=32, db_index=True)
    user = models.ForeignKey('users.Profile', db_index=True, null=True,
        blank=True)
    product = models.ForeignKey('catalog.Product', db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

class PaidUsage(models.Model):
    client_domain = models.ForeignKey('accounts.ClientDomain', db_index=True) 
    session = models.CharField(max_length=32, db_index=True)
    user = models.ForeignKey('users.Profile', db_index=True, null=True,
        blank=True)
    product = models.ForeignKey('catalog.Product', db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
