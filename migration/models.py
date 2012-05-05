from django.db import models

# Create your models here.

class DuplicateUsers(models.Model):
    duplicate = models.PositiveIntegerField()
    original = models.PositiveIntegerField()


class AccountUserMap(models.Model):
    account = models.ForeignKey('accounts.Account')
    user_id = models.PositiveIntegerField()

class ListingRateChartMap(models.Model):
    listing_id = models.CharField(max_length=32, db_index=True)
    rate_chart = models.ForeignKey('catalog.SellerRateChart', null=True, blank=True)

class AddressMap(models.Model):
    address = models.ForeignKey('locations.Address')
